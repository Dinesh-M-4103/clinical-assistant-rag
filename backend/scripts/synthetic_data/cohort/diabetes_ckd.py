"""MG25001 - type 2 diabetes with chronic kidney disease.

Planted cases: HbA1c trend across four reports, metformin dose change, a drug stopped for a
stated reason, an eGFR/CKD stage that worsens, and a preliminary report superseded by a
corrected one (potassium 6.1 on a haemolysed sample, 4.9 after recollection).
"""

from datetime import date

from synthetic_data.model import (
    NEGATIVE_START_RE,
    Bullets,
    Callout,
    DataTable,
    Fact,
    Grid,
    Heading,
    LabResult,
    LabTable,
    Para,
    PatientSpec,
    QuestionSpec,
    ReportSpec,
    Turn,
    TwoColumns,
    dose_re,
    number_re,
)

UHID = "MG25001"
HOSPITAL_DEPT_ENDO = "Department of Endocrinology & Diabetes"
HOSPITAL_DEPT_LAB = "Department of Clinical Biochemistry"

HBA1C_SEP_2025 = "8.6"
HBA1C_JAN_2026 = LabResult("HbA1c", 7.9, "%", 4.0, 5.6)
HBA1C_JUN_2026 = LabResult("HbA1c", 7.2, "%", 4.0, 5.6)
HAEMOGLOBIN = LabResult("Haemoglobin", 11.8, "g/dL", 13.0, 17.0)
EGFR_JAN = LabResult("eGFR (CKD-EPI)", 38, "mL/min/1.73 m2", low=60, decimals=0)
EGFR_JUN = LabResult("eGFR (CKD-EPI)", 40, "mL/min/1.73 m2", low=60, decimals=0)
CREATININE_JAN = LabResult("Serum creatinine", 1.9, "mg/dL", 0.7, 1.3)
CREATININE_JUN = LabResult("Serum creatinine", 1.8, "mg/dL", 0.7, 1.3)
POTASSIUM_PRELIM = LabResult("Potassium", 6.1, "mmol/L", 3.5, 5.1)
POTASSIUM_CORRECTED = LabResult("Potassium", 4.9, "mmol/L", 3.5, 5.1)


def _consultation() -> ReportSpec:
    return ReportSpec(
        file="endocrinology_consultation_2025-09-15.pdf",
        name="Endocrinology Consultation - Sep 2025",
        category="consultation",
        notes="Baseline diabetes and kidney review with medication list.",
        day=date(2025, 9, 15),
        title="Endocrinology Outpatient Consultation",
        department=HOSPITAL_DEPT_ENDO,
        author="Dr. Helen Marsh, Consultant Endocrinologist",
        blocks=(
            Heading("Reason for Visit"),
            Para(
                "Routine four-monthly review of type 2 diabetes mellitus (T2DM) with chronic "
                "kidney disease (CKD). Referred by Dr. A. Kapoor, General Practice."
            ),
            Heading("History of Presenting Illness"),
            Para(
                "Mr. Menon is a 62-year-old man with T2DM diagnosed in 2014 and hypertension (HTN) "
                "since 2011. He reports good adherence to treatment and occasional fatigue after "
                "meals. He denies polyuria, visual disturbance, chest pain or foot symptoms."
            ),
            Para(
                "**Pertinent negatives:** No history of diabetic foot ulcer or retinopathy. "
                "No history of myocardial infarction, stroke or peripheral vascular disease."
            ),
            TwoColumns(
                left=(
                    Heading("Past Medical History"),
                    Bullets(
                        (
                            "T2DM since 2014",
                            "Hypertension since 2011",
                            "CKD first noted in 2023",
                            "Dyslipidaemia",
                        )
                    ),
                ),
                right=(
                    Heading("Social History"),
                    Bullets(
                        (
                            "Retired bank clerk, lives with his wife",
                            "Never smoked; no alcohol",
                            "Vegetarian diet, walks 20 minutes daily",
                        )
                    ),
                ),
            ),
            Heading("Examination"),
            Grid(
                (
                    ("Blood pressure", "148/88 mmHg"),
                    ("Heart rate", "78 /min, regular"),
                    ("Weight", "84 kg"),
                    ("BMI", "29.1 kg/m2"),
                    ("SpO2", "98% on room air"),
                    ("Foot exam", "Monofilament sensation intact"),
                )
            ),
            Heading("Investigations"),
            Para("Results from 12 Sep 2025 (outside laboratory), reviewed at this visit."),
            DataTable(
                ("Test", "Result", "Reference", "Comment"),
                (
                    ("HbA1c", f"{HBA1C_SEP_2025} %", "4.0 - 5.6 %", "Above the 7.5 % target"),
                    ("Fasting plasma glucose", "164 mg/dL", "70 - 99 mg/dL", "High"),
                    ("Serum creatinine", "1.6 mg/dL", "0.7 - 1.3 mg/dL", "High"),
                    ("eGFR (CKD-EPI)", "46 mL/min/1.73 m2", ">= 60", "CKD stage G3a"),
                    (
                        "Urine albumin/creatinine ratio",
                        "64 mg/g",
                        "< 30 mg/g",
                        "Moderately increased",
                    ),
                ),
                widths=(2.4, 1.6, 1.6, 2.0),
            ),
            Heading("Current Medications"),
            DataTable(
                ("Medicine", "Brand", "Dose", "Frequency"),
                (
                    ("Metformin", "Glucophage", "1000 mg", "Twice daily (BD) after meals"),
                    ("Glimepiride", "Amaryl", "2 mg", "Once daily (OD) before breakfast"),
                    ("Amlodipine", "Norvasc", "5 mg", "Once daily (OD)"),
                    ("Telmisartan", "Micardis", "40 mg", "Once daily (OD)"),
                    ("Atorvastatin", "Lipitor", "20 mg", "At night"),
                ),
                widths=(1.8, 1.5, 1.2, 2.8),
            ),
            Heading("Allergies"),
            Para("No known drug allergies (NKDA)."),
            Heading("Impression"),
            Para(
                "T2DM with suboptimal glycaemic control (HbA1c 8.6 %) and CKD stage G3a with "
                "moderately increased albuminuria. Blood pressure above target."
            ),
            Heading("Plan"),
            Bullets(
                (
                    "Continue current medications; review metformin dose if eGFR falls below 45.",
                    "Repeat HbA1c, renal function and urine albumin/creatinine ratio in 4 months.",
                    "Dietitian referral; foot-care education reinforced.",
                    "Annual retinal screening to be booked with ophthalmology.",
                )
            ),
        ),
    )


def _lab_jan() -> ReportSpec:
    return ReportSpec(
        file="lab_report_2026-01-14.pdf",
        name="Biochemistry and Haematology - Jan 2026",
        category="lab",
        notes="Fasting panel: glycaemic control, lipids, renal function and blood count.",
        day=date(2026, 1, 14),
        title="Laboratory Report",
        department=HOSPITAL_DEPT_LAB,
        author="Dr. Marcus Lee, Consultant Biochemist",
        blocks=(
            Grid(
                (
                    ("Collected", "14 Jan 2026 07:42"),
                    ("Fasting status", "Fasting, 12 hours"),
                    ("Specimen", "Serum, EDTA whole blood, urine"),
                )
            ),
            Heading("Glycaemic Control"),
            LabTable(
                (
                    HBA1C_JAN_2026,
                    LabResult("Fasting plasma glucose", 138, "mg/dL", 70, 99, 0),
                )
            ),
            Heading("Haematology"),
            LabTable(
                (
                    HAEMOGLOBIN,
                    LabResult("White cell count", 7.2, "10^9/L", 4.0, 11.0),
                    LabResult("Platelets", 246, "10^9/L", 150, 400, 0),
                )
            ),
            Heading("Lipid Profile"),
            LabTable(
                (
                    LabResult("Total cholesterol", 172, "mg/dL", high=200, decimals=0),
                    LabResult("LDL cholesterol", 112, "mg/dL", high=100, decimals=0),
                    LabResult("HDL cholesterol", 41, "mg/dL", low=40, decimals=0),
                    LabResult("Triglycerides", 188, "mg/dL", high=150, decimals=0),
                )
            ),
            Heading("Renal Function and Electrolytes"),
            LabTable(
                (
                    LabResult("Urea", 52, "mg/dL", 15, 45, 0),
                    CREATININE_JAN,
                    EGFR_JAN,
                    LabResult("Sodium", 139, "mmol/L", 135, 145, 0),
                    LabResult("Potassium", 5.2, "mmol/L", 3.5, 5.1),
                    LabResult("Bicarbonate", 22, "mmol/L", 22, 29, 0),
                    LabResult("Urine albumin/creatinine ratio", 118, "mg/g", high=30, decimals=0),
                )
            ),
            Heading("Interpretation"),
            Para(
                "eGFR 38 mL/min/1.73 m2 is consistent with **CKD stage G3b**. Glycaemic control "
                "has improved since the previous review, while serum creatinine has risen. "
                "Mild hyperkalaemia; correlate clinically."
            ),
            Para("Reference ranges are adult values. H = above range, L = below range."),
        ),
    )


def _prescription() -> ReportSpec:
    return ReportSpec(
        file="prescription_2026-03-02.pdf",
        name="Prescription - Mar 2026",
        category="prescription",
        notes="Medication changes after the January kidney function result.",
        day=date(2026, 3, 2),
        title="Outpatient Prescription",
        department=HOSPITAL_DEPT_ENDO,
        author="Dr. Helen Marsh, Consultant Endocrinologist",
        blocks=(
            Grid(
                (
                    ("Diagnosis", "T2DM; CKD stage G3b; hypertension"),
                    ("Allergies", "No known drug allergies"),
                    ("Weight", "83 kg"),
                )
            ),
            Heading("Medications"),
            DataTable(
                ("Medicine", "Brand", "Dose", "Frequency", "Status", "Remarks"),
                (
                    (
                        "Metformin",
                        "Glucophage",
                        "500 mg",
                        "Twice daily (BD) after meals",
                        "Continue",
                        "Dose reduced from 1000 mg BD because eGFR is 38 mL/min/1.73 m2.",
                    ),
                    (
                        "Empagliflozin",
                        "Jardiance",
                        "10 mg",
                        "Once daily (OD) in the morning",
                        "New",
                        "Added for kidney and cardiovascular protection.",
                    ),
                    (
                        "Glimepiride",
                        "Amaryl",
                        "-",
                        "-",
                        "Stopped",
                        "Discontinued: risk of hypoglycaemia with reduced renal function.",
                    ),
                    (
                        "Telmisartan",
                        "Micardis",
                        "40 mg",
                        "Once daily (OD)",
                        "Continue",
                        "Unchanged.",
                    ),
                    ("Amlodipine", "Norvasc", "5 mg", "Once daily (OD)", "Continue", "Unchanged."),
                    (
                        "Atorvastatin",
                        "Lipitor",
                        "40 mg",
                        "At night",
                        "Continue",
                        "Dose increased from 20 mg because LDL cholesterol was 112 mg/dL.",
                    ),
                ),
                widths=(1.5, 1.3, 0.9, 1.8, 0.9, 3.0),
            ),
            Heading("Advice"),
            Bullets(
                (
                    "Sick-day rule: pause metformin and empagliflozin during vomiting, diarrhoea "
                    "or fever and restart after 48 hours of normal eating and drinking.",
                    "Check blood glucose before breakfast and at bedtime; report readings below "
                    "70 mg/dL.",
                    "Repeat renal function, potassium and HbA1c in 3 months.",
                )
            ),
        ),
    )


def _lab_june(*, corrected: bool) -> ReportSpec:
    potassium = POTASSIUM_CORRECTED if corrected else POTASSIUM_PRELIM
    if corrected:
        banner = Callout(
            "**CORRECTED REPORT - supersedes the preliminary report issued on 10 Jun 2026.** "
            "Correction: potassium. The original sample was haemolysed; the specimen was "
            "recollected and re-measured. All other results are unchanged."
        )
        title = "Laboratory Report (Corrected)"
        suffix = "corrected"
        day = date(2026, 6, 11)
        name = "Biochemistry - Jun 2026 (corrected)"
        notes = "Corrected report; replaces the preliminary biochemistry result of 10 Jun 2026."
    else:
        banner = Callout(
            "**PRELIMINARY REPORT - results are subject to verification.** "
            "Potassium: sample haemolysed, recollection requested."
        )
        title = "Laboratory Report (Preliminary)"
        suffix = "preliminary"
        day = date(2026, 6, 10)
        name = "Biochemistry - Jun 2026 (preliminary)"
        notes = "Preliminary biochemistry result; superseded by the corrected report."
    return ReportSpec(
        file=f"lab_report_2026-06-10_{suffix}.pdf",
        name=name,
        category="lab",
        notes=notes,
        day=day,
        title=title,
        department=HOSPITAL_DEPT_LAB,
        author="Dr. Marcus Lee, Consultant Biochemist",
        blocks=(
            banner,
            Grid(
                (
                    ("Collected", "10 Jun 2026 08:05"),
                    ("Fasting status", "Fasting, 12 hours"),
                    ("Specimen", "Serum and EDTA whole blood"),
                )
            ),
            Heading("Glycaemic Control"),
            LabTable((HBA1C_JUN_2026,)),
            Heading("Renal Function and Electrolytes"),
            LabTable(
                (
                    CREATININE_JUN,
                    EGFR_JUN,
                    LabResult("Sodium", 138, "mmol/L", 135, 145, 0),
                    potassium,
                    LabResult("Urine albumin/creatinine ratio", 96, "mg/g", high=30, decimals=0),
                )
            ),
            Heading("Interpretation"),
            Para(
                "Glycaemic control continues to improve. eGFR is stable at CKD stage G3b. "
                "Urinary albumin excretion remains moderately increased."
            ),
        ),
    )


def _facts() -> dict[str, Fact]:
    consult = "endocrinology_consultation_2025-09-15.pdf"
    jan = "lab_report_2026-01-14.pdf"
    pre = "lab_report_2026-06-10_preliminary.pdf"
    cor = "lab_report_2026-06-10_corrected.pdf"
    return {
        "hba1c_sep": Fact(consult, (f"HbA1c {HBA1C_SEP_2025} %",)),
        "hba1c_jan": Fact(jan, (HBA1C_JAN_2026.needle,)),
        "hba1c_jun_prelim": Fact(pre, (HBA1C_JUN_2026.needle,)),
        "hba1c_jun_corrected": Fact(cor, (HBA1C_JUN_2026.needle,)),
        "metformin_old": Fact(
            consult, ("Metformin Glucophage 1000 mg Twice daily (BD) after meals",)
        ),
        "metformin_now": Fact(
            "prescription_2026-03-02.pdf",
            ("Metformin Glucophage 500 mg Twice daily (BD) after meals Continue",),
        ),
        "glimepiride_stopped": Fact(
            "prescription_2026-03-02.pdf",
            ("Discontinued: risk of hypoglycaemia with reduced renal function.",),
        ),
        "ckd_stage": Fact(jan, ("consistent with CKD stage G3b",)),
        "no_foot_ulcer": Fact(consult, ("No history of diabetic foot ulcer or retinopathy",)),
        "potassium_corrected": Fact(cor, (POTASSIUM_CORRECTED.needle,)),
        "haemoglobin": Fact(jan, (HAEMOGLOBIN.needle,)),
    }


def _questions() -> tuple[QuestionSpec, ...]:
    other_hb = number_re("12.6", "14.9", "10.1", "11.2", "12.1")
    return (
        QuestionSpec(
            "temporal",
            "What is the patient's most recent HbA1c?",
            facts=("hba1c_jun_prelim", "hba1c_jun_corrected"),
            must_include=(number_re("7.2"),),
        ),
        QuestionSpec(
            "multi_chunk",
            "How has the patient's HbA1c changed over the course of these reports?",
            facts=("hba1c_sep", "hba1c_jan", "hba1c_jun_corrected"),
            must_include=(number_re("8.6"), number_re("7.9"), number_re("7.2")),
        ),
        QuestionSpec(
            "temporal",
            "What dose of metformin is the patient currently prescribed?",
            facts=("metformin_now",),
            must_include=(dose_re("500"), r"twice|BD|two times"),
        ),
        QuestionSpec(
            "temporal",
            "What dose of metformin was the patient taking in September 2025?",
            facts=("metformin_old",),
            must_include=(dose_re("1000"),),
        ),
        QuestionSpec(
            "abbreviation",
            "What was the glycated haemoglobin result in January 2026?",
            facts=("hba1c_jan",),
            must_include=(number_re("7.9"),),
        ),
        QuestionSpec(
            "abbreviation",
            "What stage of chronic kidney disease does the patient have?",
            facts=("ckd_stage",),
            must_include=(r"\b(?:G?3b)\b",),
        ),
        QuestionSpec(
            "table",
            "Which diabetes medicine was stopped in March 2026 and why?",
            facts=("glimepiride_stopped",),
            must_include=(r"glimepiride", r"hypoglyc"),
        ),
        QuestionSpec(
            "negation",
            "Does the patient have a history of diabetic foot ulcer or retinopathy?",
            facts=("no_foot_ulcer",),
            must_include=(r"\b(?:no|not|none|without|denies)\b",),
            must_not_include=(NEGATIVE_START_RE,),
        ),
        QuestionSpec(
            "followup",
            "And the one before that?",
            facts=("hba1c_jan",),
            must_include=(number_re("7.9"),),
            history=(
                Turn("user", "What is the patient's latest HbA1c?"),
                Turn("assistant", "The most recent HbA1c was 7.2 % on 10 Jun 2026 [C1]."),
            ),
        ),
        QuestionSpec(
            "temporal",
            "What is the patient's latest potassium level?",
            facts=("potassium_corrected",),
            must_include=(number_re("4.9"),),
        ),
        QuestionSpec(
            "cross_patient",
            "What was the patient's haemoglobin on the most recent blood count?",
            facts=("haemoglobin",),
            must_include=(number_re("11.8"),),
            must_not_include=(other_hb,),
        ),
    )


def build() -> PatientSpec:
    return PatientSpec(
        uhid=UHID,
        name="Rajesh Menon",
        age=62,
        gender="male",
        summary="Type 2 diabetes with chronic kidney disease stage G3b and hypertension.",
        reports=(
            _consultation(),
            _lab_jan(),
            _prescription(),
            _lab_june(corrected=False),
            _lab_june(corrected=True),
        ),
        facts=_facts(),
        questions=_questions(),
    )
