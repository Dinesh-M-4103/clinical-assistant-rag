"""Domain vocabulary shared by the persistence and API layers."""

from enum import StrEnum

UHID_PATTERN = r"^[A-Za-z0-9_-]{3,32}$"


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class ReportCategory(StrEnum):
    LAB = "lab"
    IMAGING = "imaging"
    DISCHARGE = "discharge"
    PRESCRIPTION = "prescription"
    CONSULTATION = "consultation"
    OTHER = "other"
