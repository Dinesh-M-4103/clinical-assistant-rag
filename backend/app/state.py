"""Process-wide collaborators, built once in the lifespan and shared by requests."""

from dataclasses import dataclass

from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.services.locks import PatientLocks
from app.services.ports import RagPort
from app.services.storage import ReportFileStore


@dataclass(frozen=True)
class AppState:
    settings: Settings
    session_factory: sessionmaker[Session]
    pipeline: RagPort
    files: ReportFileStore
    locks: PatientLocks
