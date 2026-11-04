"""Generate the synthetic patient PDFs, the upload manifest and the golden evaluation set.

Run from the repository root with the project environment:

    backend\\.venv\\Scripts\\python.exe backend\\scripts\\generate_synthetic_data.py

The output is deterministic: running it twice yields byte-identical files.
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from synthetic_data.checks import check_golden
from synthetic_data.cohort import build_cohort
from synthetic_data.facts import FactNotFoundError
from synthetic_data.golden import build_golden
from synthetic_data.manifest import build_manifest
from synthetic_data.model import PatientSpec, ReportSpec
from synthetic_data.pdf_text import PageTexts, extract_pages
from synthetic_data.render import render_report

REPO_ROOT = Path(__file__).resolve().parents[2]
SEED = 20251104
REFERENCE_PREFIX = {
    "lab": "LAB",
    "imaging": "IMG",
    "discharge": "DSC",
    "prescription": "RX",
    "consultation": "CON",
}


def _reference(patient: PatientSpec, report: ReportSpec) -> str:
    """Fake accession number, seeded per report so adding a report never shifts the others."""
    rng = random.Random(f"{SEED}:{patient.uhid}:{report.file}")
    return f"{REFERENCE_PREFIX[report.category]}-{rng.randint(10_000_000, 99_999_999)}"


def _render_all(cohort: Sequence[PatientSpec], pdf_dir: Path) -> PageTexts:
    if pdf_dir.exists():
        shutil.rmtree(pdf_dir)
    texts: PageTexts = {}
    for patient in cohort:
        patient_dir = pdf_dir / patient.uhid
        patient_dir.mkdir(parents=True)
        texts[patient.uhid] = {}
        for report in patient.reports:
            path = patient_dir / report.file
            render_report(patient, report, _reference(patient, report), path)
            texts[patient.uhid][report.file] = extract_pages(path)
    return texts


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.encode("utf-8"))


def _dump(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--out-dir", type=Path, default=REPO_ROOT / "data" / "synthetic")
    parser.add_argument(
        "--golden", type=Path, default=REPO_ROOT / "backend" / "evals" / "data" / "golden.jsonl"
    )
    args = parser.parse_args(argv)

    cohort = build_cohort()
    texts = _render_all(cohort, args.out_dir / "pdfs")
    try:
        built = build_golden(cohort, texts)
    except FactNotFoundError as error:
        print(f"ground-truth fact not found: {error}", file=sys.stderr)
        return 1
    problems = check_golden(built, cohort, texts)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1

    _write_text(args.out_dir / "manifest.json", _dump(build_manifest(cohort)))
    lines = (json.dumps(item.record.to_json(), ensure_ascii=False) for item in built)
    _write_text(args.golden, "\n".join(lines) + "\n")

    report_count = sum(len(patient.reports) for patient in cohort)
    print(f"{len(cohort)} patients, {report_count} PDFs, {len(built)} golden questions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
