"""MG25002 - atrial fibrillation and hypertension on a direct oral anticoagulant.

Planted cases: rivaroxaban dose reduced when renal function falls (brand 'Xarelto' vs generic),
the reason recorded only in a table cell, bisoprolol up-titrated during an admission, and
a patient without HbA1c results (cross-patient isolation).
"""

from datetime import date

from synthetic_data.model import (
    NEGATIVE_START_RE,
    REFUSAL_RE,
    Bullets,
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
    TwoColumns,
    dose_re,
    number_re,
)

UHID = "MG25002"
DEPT_CARDIO = "Department of Cardiology"
DEPT_LAB = "Department of Clinical Biochemistry"

CREATININE = LabResult("Serum creatinine", 1.3, "mg/dL", 0.6, 1.1)
CREATININE_CLEARANCE = LabResult(
    "Estimated creatinine clearance (Cockcroft-Gault)", 39, "mL/min", low=50, decimals=0
)
EGFR = LabResult("eGFR (CKD-EPI)", 41, "mL/min/1.73 m2", low=60, decimals=0)


def _consultation() -> ReportSpec:
    return ReportSpec(
        file="cardiology_consultation_2025-10-08.pdf",
        name="Cardiology Consultation - Oct 2025",
        category="consultation",
        notes="Paroxysmal atrial fibrillation and hypertension review; anticoagulation plan.",
        day=date(2025, 10, 8),
        title="Cardiology Outpatient Consultation",
        department=DEPT_CARDIO,
        author="Dr. Samuel Ortega, Consultant Cardiologist",
        blocks=(
            Heading("Reason for Visit"),
            Para(
                "Six-monthly follow-up of paroxysmal atrial fibrillation (AF) and hypertension "
                "(HTN). She reports palpitations two to three times a month, each lasting under "
                "an hour, without syncope."
            ),
            Heading("History"),
            Para(
                "Mrs. Iyer is a 71-year-old woman with paroxysmal AF diagnosed in March 2024 and "
                "HTN for 15 years. **Pertinent negatives:** No history of stroke, TIA or major "
                "bleeding. No history of heart failure or valvular disease."
            ),
            Para(
                "**Stroke and bleeding risk:** CHA2DS2-VASc score 3 (age 65-74, female sex, "
                "hypertension). HAS-BLED score 1 (age over 65)."
            ),
            TwoColumns(
                left=(
                    Heading("Examination"),
                    Bullets(
                        (
                            "Blood pressure 138/82 mmHg",
                            "Pulse 66 /min, irregularly irregular",
                            "Weight 62 kg",
                            "No peripheral oedema",
                        )
                    ),
                ),
                right=(
                    Heading("Tests Reviewed"),
                    Bullets(
                        (
                            "ECG: sinus rhythm 68 /min, no ST change",
                            "Echocardiogram (Sep 2025): normal LV size",
                            "Creatinine 0.9 mg/dL (05 Oct 2025), eGFR 63",
                        )
                    ),
                ),
            ),
            Heading("Current Medications"),
            DataTable(
                ("Medicine", "Brand", "Dose", "Frequency", "Indication"),
                (
                    (
                        "Rivaroxaban",
                        "Xarelto",
                        "20 mg",
                        "Once daily with evening meal",
                        "Stroke prevention in AF",
                    ),
                    ("Bisoprolol", "Concor", "2.5 mg", "Once daily in the morning", "Rate control"),
                    ("Amlodipine", "Norvasc", "10 mg", "Once daily", "Hypertension"),
                    ("Ramipril", "Tritace", "5 mg", "Once daily", "Hypertension"),
                ),
                widths=(1.5, 1.2, 0.9, 2.3, 2.0),
            ),
            Heading("Allergies"),
            Para("Shellfish: urticaria. No known drug allergies."),
            Heading("Impression"),
            Para(
                "Paroxysmal AF with infrequent, well-tolerated episodes on rate control and "
                "anticoagulation. Hypertension adequately controlled."
            ),
            Heading("Plan"),
            Bullets(
                (
                    "Continue anticoagulation and rate control unchanged.",
                    "Annual renal function check; reassess anticoagulant dose if renal function "
                    "declines.",
                    "Review in 6 months, sooner if palpitations become prolonged.",
                )
            ),
        ),
    )


def _lab() -> ReportSpec:
    return ReportSpec(
        file="lab_report_2026-02-19.pdf",
        name="Blood Count and Renal Function - Feb 2026",
        category="lab",
        notes="Annual blood count, renal function, electrolytes and thyroid function.",
        day=date(2026, 2, 19),
        title="Laboratory Report",
        department=DEPT_LAB,
        author="Dr. Marcus Lee, Consultant Biochemist",
        blocks=(
            Grid(
                (
                    ("Collected", "19 Feb 2026 09:10"),
                    ("Fasting status", "Non-fasting"),
                    ("Specimen", "Serum and EDTA whole blood"),
                )
            ),
            Heading("Haematology"),
            LabTable(
                (
                    LabResult("Haemoglobin", 12.6, "g/dL", 12.0, 15.5),
                    LabResult("White cell count", 6.8, "10^9/L", 4.0, 11.0),
                    LabResult("Platelets", 238, "10^9/L", 150, 400, 0),
                )
            ),
            Heading("Renal Function and Electrolytes"),
            LabTable(
                (
                    LabResult("Urea", 48, "mg/dL", 15, 45, 0),
                    CREATININE,
                    EGFR,
                    CREATININE_CLEARANCE,
                    LabResult("Sodium", 140, "mmol/L", 135, 145, 0),
                    LabResult("Potassium", 4.4, "mmol/L", 3.5, 5.1),
                )
            ),
            Heading("Liver and Thyroid"),
            LabTable(
                (
                    LabResult("ALT", 22, "U/L", high=35, decimals=0),
                    LabResult("TSH", 2.1, "mIU/L", 0.4, 4.0),
                )
            ),
            Heading("Interpretation"),
            Para(
                "Renal function has declined since October 2025. Estimated creatinine clearance "
                "is 39 mL/min (Cockcroft-Gault, weight 62 kg). Dose adjustment of renally "
                "cleared drugs, including rivaroxaban, should be considered."
            ),
        ),
    )


def _prescription() -> ReportSpec:
    return ReportSpec(
        file="prescription_2026-02-26.pdf",
        name="Prescription - Feb 2026",
        category="prescription",
        notes="Updated cardiac medication list with anticoagulant dose adjustment.",
        day=date(2026, 2, 26),
        title="Outpatient Prescription",
        department=DEPT_CARDIO,
        author="Dr. Samuel Ortega, Consultant Cardiologist",
        blocks=(
            Grid(
                (
                    ("Diagnosis", "Paroxysmal AF; hypertension"),
                    ("Allergies", "Shellfish (urticaria); no known drug allergies"),
                    ("Weight", "62 kg"),
                )
            ),
            Heading("Medications"),
            DataTable(
                ("Medicine", "Brand", "Dose", "Frequency", "Remarks"),
                (
                    (
                        "Rivaroxaban",
                        "Xarelto",
                        "15 mg",
                        "Once daily with evening meal",
                        "Reduced from 20 mg: creatinine clearance 39 mL/min (15-49 mL/min band).",
                    ),
                    ("Bisoprolol", "Concor", "2.5 mg", "Once daily in the morning", "Unchanged."),
                    ("Amlodipine", "Norvasc", "10 mg", "Once daily", "Unchanged."),
                    ("Ramipril", "Tritace", "5 mg", "Once daily", "Unchanged; recheck potassium."),
                ),
                widths=(1.5, 1.2, 0.9, 2.3, 3.0),
            ),
            Heading("Advice"),
            Bullets(
                (
                    "Take rivaroxaban with the evening meal; do not skip doses.",
                    "Avoid non-steroidal anti-inflammatory drugs such as ibuprofen.",
                    "Repeat renal function in 3 months.",
                )
            ),
        ),
    )


def _discharge() -> ReportSpec:
    return ReportSpec(
        file="discharge_summary_2026-07-22.pdf",
        name="Discharge Summary - Jul 2026",
        category="discharge",
        notes="Admission for atrial fibrillation with rapid ventricular response.",
        day=date(2026, 7, 22),
        title="Discharge Summary",
        department=DEPT_CARDIO,
        author="Dr. Samuel Ortega, Consultant Cardiologist",
        blocks=(
            Grid(
                (
                    ("Admitted", "18 Jul 2026"),
                    ("Discharged", "22 Jul 2026"),
                    ("Ward", "Cardiac Care Unit, then Ward 4B"),
                )
            ),
            Heading("Diagnosis"),
            Bullets(
                (
                    "Symptomatic paroxysmal atrial fibrillation with rapid ventricular response",
                    "Hypertension",
                    "Reduced renal function (eGFR 41 mL/min/1.73 m2)",
                )
            ),
            Heading("Presenting Complaint"),
            Para(
                "Four hours of palpitations with dizziness. On arrival heart rate was 148 /min "
                "and irregular, blood pressure 118/70 mmHg, oxygen saturation 97% on room air. "
                "ECG confirmed AF with rapid ventricular response. She had taken her "
                "anticoagulant that morning."
            ),
            Heading("Hospital Course"),
            Para(
                "She received an intravenous diltiazem bolus and then oral bisoprolol, which was "
                "up-titrated from 2.5 mg to 5 mg once daily. She reverted spontaneously to sinus "
                "rhythm on day 2. Serial troponin T was below 0.01 ng/mL on two samples, excluding "
                "myocardial infarction."
            ),
            Para(
                "Transthoracic echocardiography showed left ventricular ejection fraction (LVEF) "
                "58 %, mild left atrial dilatation and no significant valve disease."
            ),
            DataTable(
                ("Day", "Date", "Heart rate", "Blood pressure", "Rhythm"),
                (
                    (
                        "1",
                        "18 Jul 2026",
                        "148 /min",
                        "118/70 mmHg",
                        "AF, rapid ventricular response",
                    ),
                    (
                        "2",
                        "19 Jul 2026",
                        "92 /min",
                        "124/74 mmHg",
                        "Sinus rhythm after spontaneous reversion",
                    ),
                    ("3", "20 Jul 2026", "70 /min", "130/78 mmHg", "Sinus rhythm"),
                    ("4", "22 Jul 2026", "64 /min", "128/76 mmHg", "Sinus rhythm; discharged"),
                ),
                widths=(0.6, 1.4, 1.2, 1.6, 3.2),
            ),
            Heading("Echocardiogram Details"),
            TwoColumns(
                left=(
                    Bullets(
                        (
                            "Left ventricular end-diastolic diameter 46 mm",
                            "Left atrial diameter 42 mm (mildly dilated)",
                            "No regional wall motion abnormality",
                        )
                    ),
                ),
                right=(
                    Bullets(
                        (
                            "Aortic and mitral valves: no stenosis, trivial regurgitation",
                            "No left atrial appendage thrombus on transthoracic views",
                            "No pericardial effusion",
                        )
                    ),
                ),
            ),
            Heading("Nursing Observations (selected)"),
            DataTable(
                ("Date and time", "Heart rate", "Blood pressure", "SpO2", "Temperature"),
                (
                    ("18 Jul 2026 14:10", "148 /min", "118/70 mmHg", "97 %", "36.9 C"),
                    ("18 Jul 2026 18:00", "126 /min", "122/72 mmHg", "98 %", "36.8 C"),
                    ("19 Jul 2026 06:00", "92 /min", "124/74 mmHg", "98 %", "36.6 C"),
                    ("19 Jul 2026 14:00", "88 /min", "126/76 mmHg", "98 %", "36.7 C"),
                    ("20 Jul 2026 06:00", "70 /min", "130/78 mmHg", "99 %", "36.5 C"),
                    ("20 Jul 2026 18:00", "68 /min", "128/74 mmHg", "99 %", "36.6 C"),
                    ("21 Jul 2026 06:00", "66 /min", "126/74 mmHg", "98 %", "36.5 C"),
                    ("22 Jul 2026 06:00", "64 /min", "128/76 mmHg", "98 %", "36.6 C"),
                ),
                widths=(2.2, 1.3, 1.7, 1.0, 1.4),
            ),
            Heading("Multidisciplinary Notes"),
            Bullets(
                (
                    "Pharmacy: medicines reconciled against the general practice record; no "
                    "interactions identified with the discharge regimen.",
                    "Physiotherapy: mobilised independently on the ward by day 3.",
                    "Dietitian: low-salt diet advised; no dietary vitamin K restriction is needed "
                    "with rivaroxaban.",
                    "Nursing: no falls, pressure injuries or bleeding events during the stay.",
                )
            ),
            Heading("Patient Education"),
            Para(
                "The plan was discussed with Mrs. Iyer and her daughter. She was shown how to "
                "check her pulse, advised to avoid excess caffeine and alcohol, and given written "
                "information on atrial fibrillation and on the warning signs of stroke "
                "(facial droop, arm weakness, speech difficulty)."
            ),
            Heading("Investigations"),
            DataTable(
                ("Test", "Result", "Reference"),
                (
                    ("Troponin T (0 h and 3 h)", "< 0.01 ng/mL, < 0.01 ng/mL", "< 0.014 ng/mL"),
                    ("Haemoglobin", "12.4 g/dL", "12.0 - 15.5 g/dL"),
                    ("Potassium", "4.2 mmol/L", "3.5 - 5.1 mmol/L"),
                    ("Left ventricular ejection fraction", "58 %", ">= 55 %"),
                ),
                widths=(2.6, 2.2, 1.8),
            ),
            Heading("Medications on Discharge"),
            DataTable(
                ("Medicine", "Brand", "Dose", "Frequency", "Remarks"),
                (
                    (
                        "Rivaroxaban",
                        "Xarelto",
                        "15 mg",
                        "Once daily with evening meal",
                        "Continued; creatinine clearance remains below 50 mL/min.",
                    ),
                    (
                        "Bisoprolol",
                        "Concor",
                        "5 mg",
                        "Once daily in the morning",
                        "Increased from 2.5 mg during admission.",
                    ),
                    ("Amlodipine", "Norvasc", "10 mg", "Once daily", "Unchanged."),
                    ("Ramipril", "Tritace", "5 mg", "Once daily", "Unchanged."),
                ),
                widths=(1.5, 1.2, 0.9, 2.3, 3.0),
            ),
            Heading("Follow-up"),
            Bullets(
                (
                    "Cardiology clinic in 6 weeks with a 24-hour Holter monitor beforehand.",
                    "GP to check renal function and potassium within 2 weeks.",
                    "Return to the emergency department for palpitations lasting over 30 minutes "
                    "with chest pain, breathlessness or fainting.",
                )
            ),
        ),
    )


def _facts() -> dict[str, Fact]:
    rx = "prescription_2026-02-26.pdf"
    discharge = "discharge_summary_2026-07-22.pdf"
    consult = "cardiology_consultation_2025-10-08.pdf"
    return {
        "rivaroxaban_now": Fact(
            rx, ("Rivaroxaban Xarelto 15 mg Once daily with evening meal Reduced from 20 mg",)
        ),
        "rivaroxaban_reason": Fact(rx, ("creatinine clearance 39 mL/min (15-49 mL/min band)",)),
        "htn_meds": Fact(
            consult,
            (
                "Amlodipine Norvasc 10 mg Once daily Hypertension",
                "Ramipril Tritace 5 mg Once daily Hypertension",
            ),
        ),
        "no_stroke": Fact(consult, ("No history of stroke, TIA or major bleeding",)),
        "bisoprolol_old": Fact(consult, ("Bisoprolol Concor 2.5 mg",)),
        "bisoprolol_new": Fact(
            discharge, ("Bisoprolol Concor 5 mg Once daily in the morning Increased from 2.5 mg",)
        ),
        "lvef": Fact(discharge, ("Left ventricular ejection fraction 58 %",)),
    }


def _questions() -> tuple[QuestionSpec, ...]:
    return (
        QuestionSpec(
            "temporal",
            "What dose of Xarelto is the patient taking now?",
            facts=("rivaroxaban_now",),
            must_include=(dose_re("15"),),
        ),
        QuestionSpec(
            "table",
            "Why was the rivaroxaban dose reduced?",
            facts=("rivaroxaban_reason",),
            must_include=(r"creatinine clearance|CrCl|renal|kidney", number_re("39")),
        ),
        QuestionSpec(
            "abbreviation",
            "How is the patient's high blood pressure treated?",
            facts=("htn_meds",),
            must_include=(r"amlodipine", r"ramipril"),
        ),
        QuestionSpec(
            "negation",
            "Has the patient ever had a stroke or a major bleed?",
            facts=("no_stroke",),
            must_include=(r"\b(?:no|not|none|without|never)\b",),
            must_not_include=(NEGATIVE_START_RE,),
        ),
        QuestionSpec(
            "multi_chunk",
            "How has the bisoprolol dose changed?",
            facts=("bisoprolol_old", "bisoprolol_new"),
            must_include=(dose_re("2.5"), dose_re("5")),
        ),
        QuestionSpec(
            "numeric",
            "What was the left ventricular ejection fraction on the echocardiogram?",
            facts=("lvef",),
            must_include=(r"58\s*%",),
        ),
        QuestionSpec(
            "cross_patient",
            "What is the patient's latest HbA1c?",
            must_include=(REFUSAL_RE,),
            must_not_include=(number_re("8.6", "7.9", "7.2"),),
            answerable=False,
        ),
        QuestionSpec(
            "unanswerable",
            "What is the patient's blood group?",
            must_include=(REFUSAL_RE,),
            must_not_include=(r"\bO\s*(?:positive|pos|\+)",),
            answerable=False,
        ),
    )


def build() -> PatientSpec:
    return PatientSpec(
        uhid=UHID,
        name="Meera Iyer",
        age=71,
        gender="female",
        summary="Paroxysmal atrial fibrillation and hypertension on a direct oral anticoagulant.",
        reports=(_consultation(), _lab(), _prescription(), _discharge()),
        facts=_facts(),
        questions=_questions(),
    )
