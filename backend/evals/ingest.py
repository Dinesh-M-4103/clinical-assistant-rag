"""Ingest the synthetic corpus into a throw-away vector store, straight through ``RagPipeline``.

Report ids are ``<uhid>/<file name>`` so that a retrieved chunk can be traced back to the
golden set's file names and to its owning patient without a lookup table.
"""

from pathlib import Path

from app.rag.pipeline import RagPipeline
from evals.dataset import ManifestPatient


def report_id_for(patient_id: str, file_name: str) -> str:
    return f"{patient_id}/{file_name}"


def file_name_of(report_id: str) -> str:
    """The report's PDF file name, as the golden set refers to it."""
    return report_id.split("/", 1)[1]


def owner_of(report_id: str) -> str:
    """The patient a report belongs to."""
    return report_id.split("/", 1)[0]


def ingest_corpus(pipeline: RagPipeline, patients: list[ManifestPatient], pdf_root: Path) -> int:
    """Ingest every report of every patient; returns the total number of chunks stored."""
    chunks = 0
    for patient in patients:
        for report in patient.reports:
            result = pipeline.ingest_pdf(
                patient_id=patient.uhid,
                report_id=report_id_for(patient.uhid, report.file),
                report_name=report.name,
                category=report.category,
                pdf_path=pdf_root / patient.uhid / report.file,
            )
            chunks += result.chunk_count
    return chunks
