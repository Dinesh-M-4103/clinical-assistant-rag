"""Command-line entry point.

python -m evals.run                                  # retrieval ablation, zero LLM calls
python -m evals.run --answers --modes hybrid_rerank  # plus answer quality (live, rate limited)
"""

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from datetime import datetime
from typing import Any, get_args

from app.rag.config import RagSettings, RetrievalMode
from app.rag.errors import RagError
from app.rag.llm import GeminiClient
from app.rag.pipeline import RagPipeline
from app.rag.ratelimit import RateLimiter
from evals import report
from evals.answer_eval import evaluate_answers, pass_rate_by_type, summarise_answers
from evals.dataset import GoldenQuestion, load_golden, load_manifest
from evals.llm_cache import CachedLLM
from evals.paths import GOLDEN_PATH, LLM_CACHE_PATH, MANIFEST_PATH, RESULTS_DIR
from evals.pipelines import app_rag_settings, ingested_pipelines
from evals.retrieval_eval import (
    GATE_SWEEP,
    evaluate_retrieval,
    summarise_by_mode,
    summarise_by_type,
    summarise_gate,
)

ALL_MODES: tuple[RetrievalMode, ...] = get_args(RetrievalMode)
DEFAULT_MODE: RetrievalMode = "hybrid_rerank"
DEFAULT_MAX_LIVE_CALLS = 60


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    questions = load_golden(GOLDEN_PATH)[: args.limit]
    settings = app_rag_settings()
    retrieval_modes: list[RetrievalMode] = [] if args.skip_retrieval else list(args.modes)
    pipeline_modes = retrieval_modes + ([DEFAULT_MODE] if args.answers else [])
    cached_llm = _cached_llm(settings, args.max_live_calls) if args.answers else None

    results: dict[str, Any] = {"meta": _meta(settings, questions, pipeline_modes)}
    markdown = [f"# Evaluation run {results['meta']['timestamp']}", ""]
    patients = load_manifest(MANIFEST_PATH)
    try:
        with ingested_pipelines(settings, pipeline_modes, patients, cached_llm) as pipelines:
            if retrieval_modes:
                selected = {mode: pipelines[mode] for mode in retrieval_modes}
                _run_retrieval(selected, questions, settings, results, markdown)
            if cached_llm is not None:
                _run_answers(pipelines[DEFAULT_MODE], questions, results, markdown)
                results["meta"]["live_llm_calls"] = cached_llm.live_calls
                results["meta"]["llm_cache_hits"] = cached_llm.cache_hits
    except RagError as error:
        print(f"Evaluation stopped: {error}", file=sys.stderr)
        return 2
    text = "\n".join(markdown)
    _write(results, text, update_latest=args.latest)
    print(text)
    return 0


def _run_retrieval(
    pipelines: Mapping[RetrievalMode, RagPipeline],
    questions: list[GoldenQuestion],
    settings: RagSettings,
    results: dict[str, Any],
    markdown: list[str],
) -> None:
    records = evaluate_retrieval(pipelines, questions)
    by_mode, by_type = summarise_by_mode(records), summarise_by_type(records)
    gate = summarise_gate(records, questions, [settings.min_rerank_score, *GATE_SWEEP])
    results["retrieval"] = {
        "by_mode": by_mode,
        "by_type": by_type,
        "gate": gate,
        "records": records,
    }
    markdown += [
        "## Retrieval ablation",
        report.ablation_table(by_mode),
        "",
        "## Retrieval by question type",
        report.type_table(by_type),
        "",
        "## Relevance gate (first row: configured threshold; follow-ups excluded)",
        report.gate_table(gate),
        "",
    ]


def _run_answers(
    pipeline: RagPipeline,
    questions: list[GoldenQuestion],
    results: dict[str, Any],
    markdown: list[str],
) -> None:
    verdicts = evaluate_answers(pipeline, questions)
    summary = summarise_answers(verdicts)
    by_type = pass_rate_by_type(verdicts)
    results["answers"] = {"summary": summary, "by_type": by_type, "verdicts": verdicts}
    markdown += [
        f"## Answer quality ({DEFAULT_MODE})",
        report.answer_lines(summary),
        "",
        report.answer_type_table(by_type),
        "",
    ]


def _cached_llm(settings: RagSettings, max_live_calls: int) -> CachedLLM:
    live = GeminiClient(
        model=settings.llm_model,
        api_key=settings.gemini_api_key,
        backend=settings.gemini_backend,
        limiter=RateLimiter(settings.gemini_max_rpm),
    )
    return CachedLLM(live, LLM_CACHE_PATH, max_live_calls=max_live_calls)


def _meta(
    settings: RagSettings, questions: Sequence[GoldenQuestion], modes: Sequence[str]
) -> dict[str, Any]:
    settings_view = {
        key: value
        for key, value in asdict(settings).items()
        if key not in {"gemini_api_key", "chroma_dir", "hf_cache_dir"}
    }
    return {
        "timestamp": datetime.now().strftime("%Y%m%d-%H%M%S"),
        "questions": len(questions),
        "modes": list(modes),
        "settings": settings_view,
    }


def _write(results: dict[str, Any], markdown: str, *, update_latest: bool) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = results["meta"]["timestamp"]
    payload = json.dumps(_jsonable(results), indent=2)
    (RESULTS_DIR / f"{stamp}.md").write_text(markdown, encoding="utf-8")
    (RESULTS_DIR / f"{stamp}.json").write_text(payload, encoding="utf-8")
    if update_latest:
        (RESULTS_DIR / "latest.json").write_text(payload, encoding="utf-8")


def _jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m evals.run", description=__doc__)
    parser.add_argument("--modes", nargs="+", choices=ALL_MODES, default=list(ALL_MODES))
    parser.add_argument("--answers", action="store_true", help="also evaluate generated answers")
    parser.add_argument("--limit", type=int, default=None, help="only the first N questions")
    parser.add_argument("--skip-retrieval", action="store_true", help="answers only")
    parser.add_argument("--latest", action="store_true", help="also write results/latest.json")
    parser.add_argument("--max-live-calls", type=int, default=DEFAULT_MAX_LIVE_CALLS)
    args = parser.parse_args(argv)
    if args.skip_retrieval and not args.answers:
        parser.error("--skip-retrieval needs --answers, otherwise there is nothing to run")
    return args


if __name__ == "__main__":
    sys.exit(main())
