"""Report lifecycle: upload + ingestion, lookup, file access and deletion."""

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

import structlog
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.errors import BadRequestError, NotFoundError
from app.db.models import Report
from app.domain import ReportCategory
from app.rag.errors import InvalidPdfError, NoExtractableTextError
from app.services.filenames import sanitize_filename
from app.services.locks import PatientLocks
from app.services.patients import PatientService
from app.services.ports import RagPort
from app.services.storage import ReportFileStore

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class ReportUpload:
    """An incoming PDF plus the metadata the clinician typed in."""

    stream: BinaryIO
    filename: str | None
    name: str
    category: ReportCategory
    notes: str | None


class ReportService:
    def __init__(
        self,
        session: Session,
        pipeline: RagPort,
        patients: PatientService,
        files: ReportFileStore,
        locks: PatientLocks,
    ) -> None:
        self._session = session
        self._pipeline = pipeline
        self._patients = patients
        self._files = files
        self._locks = locks

    def list_for_patient(self, uhid: str) -> list[Report]:
        self._patients.get(uhid)
        query = (
            select(Report)
            .where(Report.uhid == uhid)
            .order_by(Report.uploaded_at.desc(), text("reports.rowid DESC"))
        )
        return list(self._session.scalars(query))

    def get(self, uhid: str, report_id: str) -> Report:
        """Look a report up *within* its patient, so another patient's id is a 404."""
        query = select(Report).where(Report.uhid == uhid, Report.report_id == report_id)
        report = self._session.scalars(query).one_or_none()
        if report is None:
            raise NotFoundError("Report not found.")
        return report

    def locate_file(self, uhid: str, report_id: str) -> tuple[Report, Path]:
        report = self.get(uhid, report_id)
        path = self._files.path_for(uhid, report_id)
        if not path.is_file():
            raise NotFoundError("The report file is no longer available.")
        return report, path

    def upload(self, uhid: str, upload: ReportUpload) -> Report:
        """Store, ingest and register a PDF; any failure leaves no trace behind.

        File, vectors and row are created in that order and the row is the
        commit point, so on failure only the file and vectors need discarding.
        """
        self._patients.get(uhid)
        report_id = str(uuid4())
        size_bytes = self._files.save(upload.stream, uhid, report_id)

        with self._locks.hold(uhid):
            try:
                result = self._pipeline.ingest_pdf(
                    patient_id=uhid,
                    report_id=report_id,
                    report_name=upload.name,
                    category=upload.category.value,
                    pdf_path=self._files.path_for(uhid, report_id),
                )
                report = Report(
                    report_id=report_id,
                    uhid=uhid,
                    name=upload.name,
                    category=upload.category.value,
                    notes=upload.notes,
                    original_filename=sanitize_filename(upload.filename),
                    page_count=result.page_count,
                    chunk_count=result.chunk_count,
                    size_bytes=size_bytes,
                )
                self._session.add(report)
                self._session.commit()
            except NoExtractableTextError as exc:
                self._discard(uhid, report_id)
                raise BadRequestError(
                    "no_extractable_text",
                    "The PDF has no extractable text (it may be a scanned image).",
                ) from exc
            except InvalidPdfError as exc:
                self._discard(uhid, report_id)
                raise BadRequestError("invalid_pdf", "The PDF is corrupt or encrypted.") from exc
            except Exception:
                self._discard(uhid, report_id)
                raise
        return report

    def delete(self, uhid: str, report_id: str) -> None:
        """Remove row and vectors atomically, then the file (best-effort)."""
        with self._locks.hold(uhid):
            report = self.get(uhid, report_id)
            self._session.delete(report)
            self._session.flush()
            try:
                self._pipeline.delete_report(patient_id=uhid, report_id=report_id)
                self._session.commit()
            except Exception:
                self._session.rollback()
                raise
            self._files.delete(uhid, report_id)

    def _discard(self, uhid: str, report_id: str) -> None:
        """Undo a failed ingestion: roll back the session, drop vectors and the file."""
        self._session.rollback()
        try:
            self._pipeline.delete_report(patient_id=uhid, report_id=report_id)
        except Exception:
            logger.exception("vector_cleanup_failed", uhid=uhid, report_id=report_id)
        try:
            self._files.delete(uhid, report_id)
        except OSError:
            logger.exception("file_cleanup_failed", uhid=uhid, report_id=report_id)
