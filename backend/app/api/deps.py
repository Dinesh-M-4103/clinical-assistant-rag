"""FastAPI dependencies: the single place where services are wired together."""

from collections.abc import Iterator
from typing import Annotated, cast
from uuid import UUID

from fastapi import Depends, Request
from fastapi import Path as PathParam
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.domain import UHID_PATTERN
from app.services.chat import ChatService
from app.services.patients import PatientService
from app.services.ports import RagPort
from app.services.reports import ReportService
from app.state import AppState

UhidPath = Annotated[
    str, PathParam(pattern=UHID_PATTERN, description="Hospital patient id (3-32 chars).")
]
ReportIdPath = Annotated[UUID, PathParam(description="Server-generated report id.")]


def get_state(request: Request) -> AppState:
    return cast(AppState, request.app.state.container)


StateDep = Annotated[AppState, Depends(get_state)]


def get_settings(state: StateDep) -> Settings:
    return state.settings


def get_pipeline(state: StateDep) -> RagPort:
    return state.pipeline


def get_session(state: StateDep) -> Iterator[Session]:
    with state.session_factory() as session:
        yield session


SettingsDep = Annotated[Settings, Depends(get_settings)]
PipelineDep = Annotated[RagPort, Depends(get_pipeline)]
SessionDep = Annotated[Session, Depends(get_session)]


def get_patient_service(
    session: SessionDep, pipeline: PipelineDep, state: StateDep
) -> PatientService:
    return PatientService(session, pipeline, state.files, state.locks)


PatientServiceDep = Annotated[PatientService, Depends(get_patient_service)]


def get_report_service(
    session: SessionDep, pipeline: PipelineDep, patients: PatientServiceDep, state: StateDep
) -> ReportService:
    return ReportService(session, pipeline, patients, state.files, state.locks)


def get_chat_service(pipeline: PipelineDep, patients: PatientServiceDep) -> ChatService:
    return ChatService(pipeline, patients)


ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]
ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
