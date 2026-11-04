"""The upload manifest consumed by the seed script."""

from collections.abc import Sequence
from typing import Any

from synthetic_data.model import PatientSpec


def build_manifest(cohort: Sequence[PatientSpec]) -> dict[str, Any]:
    return {
        "patients": [
            {
                "uhid": patient.uhid,
                "name": patient.name,
                "age": patient.age,
                "gender": patient.gender,
                "summary": patient.summary,
                "reports": [
                    {
                        "file": report.file,
                        "name": report.name,
                        "category": report.category,
                        "notes": report.notes,
                        "date": report.day.isoformat(),
                    }
                    for report in sorted(patient.reports, key=lambda r: (r.day, r.file))
                ],
            }
            for patient in cohort
        ]
    }
