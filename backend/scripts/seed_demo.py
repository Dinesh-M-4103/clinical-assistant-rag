"""Load the synthetic demo patients and their PDFs into a running backend.

Everything goes through the public HTTP API, exactly like the UI does, so the script
doubles as a smoke test of ingestion. It is idempotent: patients and reports that
already exist are skipped.

    backend\\.venv\\Scripts\\python.exe backend\\scripts\\seed_demo.py [--base-url http://localhost:8000]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

REPO_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_DIR = REPO_ROOT / "data" / "synthetic"
API_PREFIX = "/api/v1"
UPLOAD_TIMEOUT_SECONDS = 300.0


@dataclass
class SeedSummary:
    """Running totals, printed once the run is over."""

    patients_created: int = 0
    reports_uploaded: int = 0
    reports_skipped: int = 0
    ingest_seconds: float = 0.0


def seed(client: httpx.Client, manifest: dict[str, Any], pdf_root: Path) -> SeedSummary:
    """Upload every patient and report in ``manifest`` that the backend does not have yet."""
    existing = {patient["uhid"] for patient in _get(client, "/patients")}
    summary = SeedSummary()
    for patient in manifest["patients"]:
        uhid = patient["uhid"]
        if uhid in existing:
            print(f"{uhid}  {patient['name']}: already present")
        else:
            _post_patient(client, patient)
            summary.patients_created += 1
            print(f"{uhid}  {patient['name']}: created")
        _seed_reports(client, patient, pdf_root / uhid, summary)
    return summary


def _seed_reports(
    client: httpx.Client, patient: dict[str, Any], pdf_dir: Path, summary: SeedSummary
) -> None:
    uhid = patient["uhid"]
    uploaded = {report["original_filename"] for report in _get(client, f"/patients/{uhid}/reports")}
    reports = patient["reports"]
    for index, report in enumerate(reports, start=1):
        label = f"  [{index}/{len(reports)}] {report['file']}"
        if report["file"] in uploaded:
            print(f"{label}: skipped (already uploaded)")
            summary.reports_skipped += 1
            continue
        started = time.perf_counter()
        created = _upload_report(client, uhid, report, pdf_dir / report["file"])
        seconds = time.perf_counter() - started
        pages, chunks = created["page_count"], created["chunk_count"]
        print(f"{label}: {pages} pages, {chunks} chunks in {seconds:.1f}s")
        summary.reports_uploaded += 1
        summary.ingest_seconds += seconds


def _get(client: httpx.Client, path: str) -> list[dict[str, Any]]:
    response = client.get(f"{API_PREFIX}{path}")
    response.raise_for_status()
    result: list[dict[str, Any]] = response.json()
    return result


def _post_patient(client: httpx.Client, patient: dict[str, Any]) -> None:
    fields = ("uhid", "name", "age", "gender", "summary")
    response = client.post(f"{API_PREFIX}/patients", json={key: patient[key] for key in fields})
    response.raise_for_status()


def _upload_report(
    client: httpx.Client, uhid: str, report: dict[str, Any], pdf_path: Path
) -> dict[str, Any]:
    data = {key: report[key] for key in ("name", "category", "notes") if report.get(key)}
    with pdf_path.open("rb") as handle:
        response = client.post(
            f"{API_PREFIX}/patients/{uhid}/reports",
            data=data,
            files={"file": (pdf_path.name, handle, "application/pdf")},
            timeout=UPLOAD_TIMEOUT_SECONDS,
        )
    response.raise_for_status()
    created: dict[str, Any] = response.json()
    return created


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0] if __doc__ else None)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--manifest", type=Path, default=SYNTHETIC_DIR / "manifest.json")
    args = parser.parse_args(argv)

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    pdf_root = args.manifest.parent / "pdfs"
    try:
        with httpx.Client(base_url=args.base_url, timeout=30.0) as client:
            summary = seed(client, manifest, pdf_root)
    except httpx.HTTPStatusError as error:
        print(
            f"Request failed: {error.response.status_code} {error.response.text}", file=sys.stderr
        )
        return 1
    except httpx.TransportError as error:
        print(f"Cannot reach the backend at {args.base_url}: {error}", file=sys.stderr)
        return 1

    print(
        f"Done: {summary.patients_created} patients created, {summary.reports_uploaded} reports "
        f"uploaded ({summary.ingest_seconds:.1f}s of ingestion), {summary.reports_skipped} skipped."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
