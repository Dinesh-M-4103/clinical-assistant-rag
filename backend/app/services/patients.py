"""Patient lifecycle: registration, lookup and cascading deletion."""

import structlog
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.db.models import Patient
from app.schemas.patients import PatientCreate
from app.services.locks import PatientLocks
from app.services.ports import RagPort
from app.services.storage import ReportFileStore

logger = structlog.get_logger(__name__)


class PatientService:
    def __init__(
        self,
        session: Session,
        pipeline: RagPort,
        files: ReportFileStore,
        locks: PatientLocks,
    ) -> None:
        self._session = session
        self._pipeline = pipeline
        self._files = files
        self._locks = locks

    def list_all(self) -> list[Patient]:
        # rowid breaks ties between rows created within the same clock tick.
        query = select(Patient).order_by(Patient.created_at.desc(), text("patients.rowid DESC"))
        return list(self._session.scalars(query))

    def get(self, uhid: str) -> Patient:
        patient = self._session.get(Patient, uhid)
        if patient is None:
            raise NotFoundError(f"Patient {uhid} not found.")
        return patient

    def create(self, data: PatientCreate) -> Patient:
        patient = Patient(**data.model_dump())
        self._session.add(patient)
        try:
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise ConflictError("patient_exists", f"Patient {data.uhid} already exists.") from exc
        return patient

    def delete(self, uhid: str) -> None:
        """Remove the patient, their report rows, vectors and files.

        The row deletion and the vector deletion share one transaction boundary:
        if Chroma fails the rows are rolled back, so the two stores never disagree.
        Files go last and are best-effort because nothing references them anymore.
        """
        with self._locks.hold(uhid):
            patient = self.get(uhid)
            self._session.delete(patient)
            self._session.flush()
            try:
                self._pipeline.delete_patient(patient_id=uhid)
                self._session.commit()
            except Exception:
                self._session.rollback()
                raise
            self._files.delete_patient(uhid)
