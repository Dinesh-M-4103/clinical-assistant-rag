from fastapi import APIRouter, status

from app.api.deps import PatientServiceDep, UhidPath
from app.db import models
from app.schemas import patients as schemas
from app.schemas.errors import error_responses

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("", response_model=list[schemas.Patient], summary="List patients, newest first")
def list_patients(service: PatientServiceDep) -> list[models.Patient]:
    return service.list_all()


@router.post(
    "",
    response_model=schemas.Patient,
    status_code=status.HTTP_201_CREATED,
    summary="Register a patient",
    responses=error_responses(409, 422),
)
def create_patient(data: schemas.PatientCreate, service: PatientServiceDep) -> models.Patient:
    return service.create(data)


@router.get(
    "/{uhid}",
    response_model=schemas.Patient,
    summary="Get one patient",
    responses=error_responses(404, 422),
)
def get_patient(uhid: UhidPath, service: PatientServiceDep) -> models.Patient:
    return service.get(uhid)


@router.delete(
    "/{uhid}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a patient with all reports, files and vectors",
    responses=error_responses(404, 422),
)
def delete_patient(uhid: UhidPath, service: PatientServiceDep) -> None:
    service.delete(uhid)
