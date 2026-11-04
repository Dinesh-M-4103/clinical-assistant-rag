from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.domain import UHID_PATTERN, Gender

Uhid = Annotated[str, Field(pattern=UHID_PATTERN, description="Hospital patient id, 3-32 chars.")]


class PatientCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    uhid: Uhid
    name: Annotated[str, Field(min_length=1, max_length=200)]
    age: Annotated[int, Field(ge=0, le=130)]
    gender: Gender
    summary: Annotated[str | None, Field(max_length=2000)] = None


class Patient(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uhid: str
    name: str
    age: int
    gender: Gender
    summary: str | None
    report_count: int
    created_at: datetime
