from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import StringConstraints

from app.api.deps import ReportIdPath, ReportServiceDep, UhidPath
from app.db import models
from app.domain import ReportCategory
from app.schemas import reports as schemas
from app.schemas.errors import error_responses
from app.services.reports import ReportUpload

router = APIRouter(prefix="/patients/{uhid}/reports", tags=["reports"])

ReportName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
ReportNotes = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]


@router.get(
    "",
    response_model=list[schemas.Report],
    summary="List a patient's reports, newest first",
    responses=error_responses(404, 422),
)
def list_reports(uhid: UhidPath, service: ReportServiceDep) -> list[models.Report]:
    return service.list_for_patient(uhid)


@router.post(
    "",
    response_model=schemas.Report,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF and index it for retrieval",
    responses=error_responses(400, 404, 413, 415, 422),
)
def upload_report(
    uhid: UhidPath,
    service: ReportServiceDep,
    file: Annotated[UploadFile, File(description="The PDF report.")],
    name: Annotated[ReportName, Form(description="Display name, e.g. 'CBC Report'.")],
    category: Annotated[ReportCategory, Form()],
    notes: Annotated[ReportNotes | None, Form()] = None,
) -> models.Report:
    upload = ReportUpload(
        stream=file.file,
        filename=file.filename,
        name=name,
        category=category,
        notes=notes or None,
    )
    return service.upload(uhid, upload)


@router.get(
    "/{report_id}/file",
    summary="Download the original PDF (inline)",
    response_class=FileResponse,
    responses={200: {"content": {"application/pdf": {}}}, **error_responses(404, 422)},
)
def download_report(
    uhid: UhidPath, report_id: ReportIdPath, service: ReportServiceDep
) -> FileResponse:
    report, path = service.locate_file(uhid, str(report_id))
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=report.original_filename,
        content_disposition_type="inline",
        headers={"X-Content-Type-Options": "nosniff"},
    )


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a report with its file and vectors",
    responses=error_responses(404, 422),
)
def delete_report(uhid: UhidPath, report_id: ReportIdPath, service: ReportServiceDep) -> None:
    service.delete(uhid, str(report_id))
