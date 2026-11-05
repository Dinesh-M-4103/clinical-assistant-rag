# Evaluation harness

Measures how well the RAG pipeline finds and uses the evidence in a patient's reports. It runs the
real `RagPipeline` over the synthetic corpus in `data/synthetic/` and the 52 golden questions in
`evals/data/golden.jsonl`. There is no HTTP layer and no LLM-as-judge: every check is a metric over
ranked pages or a regular expression.

## Running it

From the repo root (any shell):

```bash
make eval                          # Git Bash / macOS / Linux
.\scripts\dev.ps1 eval             # Windows PowerShell
```

Or directly, from `backend/` (`HF_HOME=backend/.cache/huggingface` keeps models inside the repo):

```bash
python -m evals.run                                  # retrieval ablation, all 4 modes, 0 LLM calls
python -m evals.run --modes hybrid hybrid_rerank     # a subset of modes
python -m evals.run --limit 10                       # first 10 questions only
python -m evals.run --answers                        # retrieval + answer quality (live LLM)
python -m evals.run --answers --skip-retrieval       # answer quality only
python -m evals.run --latest                         # also overwrite results/latest.json
```

The `make` and `dev.ps1` entries forward extra arguments (`make eval ARGS="--answers"`,
`.\scripts\dev.ps1 eval --answers`).

Every run writes `results/<timestamp>.json` (full per-question records) and `results/<timestamp>.md`
(the tables). Only `results/latest.json` is committed; refresh it with `--latest` after a full run.

Retrieval-only runs take about two minutes on CPU, most of it loading models and ingesting the
corpus into a temporary Chroma directory that is deleted afterwards.

## Answer-quality run (costs LLM quota)

`--answers` asks every golden question through the default mode (`hybrid_rerank`) and checks the
answers. It has **not been run yet**; run it once when the quota is fresh:

```bash
python -m evals.run --answers --latest
```

Expected cost: about 48 live Gemini calls (52 questions, minus the ~7 that the relevance gate
answers without the model, plus 2 follow-up rewrites). The run is safe on a free-tier key:

- `GeminiClient` enforces `GEMINI_MAX_RPM` (default 8), so it takes roughly six minutes.
- `--max-live-calls` (default 60) aborts before spending more than that.
- Answers are cached in `backend/.cache/llm_cache.json`, keyed by a hash of model and prompt. A
  re-run, or a run resumed after a quota error, only pays for prompts that are new.
- A daily-quota error stops the run with a clear message instead of retrying.

What it reports (all deterministic):

| Metric | Definition |
|---|---|
| must_include / must_not_include pass rate | Every `must_include` regex matches the answer and no `must_not_include` regex does (case-insensitive). |
| Unanswerable handling | Questions with `answerable: false` pass when the answer matches a refusal pattern ("not found", "no information", "cannot", ...) and states no forbidden value, such as another patient's result. The relevance gate's canned reply matches the pattern. |
| Injection resistance | Injection questions whose answer contains none of the forbidden text. |
| Citation precision | Cited chunks (`cited: true`) whose (report, page) is in the golden `expected_reports` x `expected_pages`. |
| Cross-patient leak rate | Any retrieved chunk owned by another patient, or a cross-patient question whose answer states the other patient's value. Must be 0. |

## Metrics and conventions

- A retrieved chunk is a **hit** when its (report file, page) pair is one of the question's expected
  sources. hit@k is the share of questions with a hit in the top k; MRR is the mean of 1 / rank of
  the first hit (top 5); recall@k is the share of expected *reports* with a hit in the top k.
- Questions the records cannot answer have no expected sources, so they are left out of the
  retrieval metrics (48 of 52 are scored) and feed the relevance-gate table instead.
- Retrieval searches the literal question text. Follow-ups ("And the one before that?") need an LLM
  rewrite to be searchable, so their retrieval numbers are a lower bound and the gate table
  excludes them.
- All four modes share one embedder, reranker and vector store; only the ranking differs.

## Layout

| Module | Responsibility |
|---|---|
| `dataset.py` | Typed loading of `golden.jsonl` and the corpus manifest. |
| `metrics.py` | Pure retrieval metrics over ranked (report, page) sources. |
| `ingest.py` | Ingest the corpus through `RagPipeline`; report ids are `<uhid>/<file>`. |
| `pipelines.py` | One pipeline per mode over a throw-away Chroma store. |
| `retrieval_eval.py` | Run retrieval per mode, aggregate by mode and question type, replay the relevance gate. |
| `answer_checks.py` | Deterministic checks for one answer. |
| `answer_eval.py` | Ask every question and aggregate the checks. |
| `llm_cache.py` | Disk cache and live-call budget around the real LLM client. |
| `report.py` | Markdown tables. |
| `run.py` | The CLI. |

Unit tests (fake LLM, no network): `python -m pytest tests/evals`. The results and their analysis
are in [`docs/eval-report.md`](../../docs/eval-report.md).
