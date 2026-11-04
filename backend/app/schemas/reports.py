from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field

from app.domain import ReportCategory


class Report(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    report_id: str
    uhid: str
    name: str
    category: ReportCategory
    notes: str | None
    original_filename: str
    page_count: int
    chunk_count: int
    size_bytes: int
    uploaded_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def file_url(self) -> str:
        return f"/api/v1/patients/{self.uhid}/reports/{self.report_id}/file"
