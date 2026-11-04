"""The six synthetic patients, in UHID order."""

from synthetic_data.cohort import (
    af_hypertension,
    copd,
    diabetes_ckd,
    oncology,
    orthopaedic,
    pregnancy,
)
from synthetic_data.model import PatientSpec


def build_cohort() -> tuple[PatientSpec, ...]:
    modules = (diabetes_ckd, af_hypertension, copd, orthopaedic, pregnancy, oncology)
    return tuple(module.build() for module in modules)
