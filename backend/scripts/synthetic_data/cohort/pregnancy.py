"""MG25005 - antenatal care with gestational diabetes and iron deficiency.

Planted cases: an HbA1c of a non-diabetic patient (same lab name as MG25001, different value),
OGTT values only in a table, gestational age and due date derived from the LMP, an iron dose
that doubles between visits, and a latex allergy that is not a drug allergy.
"""

from datetime import date

from synthetic_data.model import (
    NEGATIVE_START_RE,
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
    date_re,
    due_date,
    fmt_date,
    gestation,
    number_re,
)

UHID = "MG25005"
DEPT_OBS = "Department of Obstetrics and Gynaecology"
DEPT_LAB = "Department of Clinical Biochemistry"
DEPT_IMAGING = "Department of Radiology and Fetal Medicine"

LMP = date(2026, 3, 29)
EDD = due_date(LMP)

HBA1C = LabResult("HbA1c", 5.1, "%", 4.0, 5.6)
OGTT_FASTING = LabResult("Glucose, fasting", 98, "mg/dL", high=92, decimals=0)
OGTT_1H = LabResult("Glucose, 1 hour", 182, "mg/dL", high=180, decimals=0)
OGTT_2H = LabResult("Glucose, 2 hour", 158, "mg/dL", high=153, decimals=0)
FERRITIN_SEP = LabResult("Ferritin", 14, "ug/L", 15, 150, 0)


def _booking() -> ReportSpec:
    booking_day = date(2026, 6, 2)
    return ReportSpec(
        file="antenatal_booking_visit_2026-06-02.pdf",
        name="Antenatal Booking Visit - Jun 2026",
        category="consultation",
        notes="Booking history, risk assessment and antenatal plan.",
        day=booking_day,
        title="Antenatal Booking Consultation",
        department=DEPT_OBS,
        author="Dr. Laura Whitcombe, Consultant Obstetrician",
        blocks=(
            Grid(
                (
                    ("Gravida / para", "G2 P1"),
                    ("Last menstrual period", fmt_date(LMP)),
                    ("Gestation at booking", gestation(LMP, booking_day)),
                    ("Estimated delivery date", f"{fmt_date(EDD)}"),
                    ("Blood pressure", "112/68 mmHg"),
                    ("BMI", "24.1 kg/m2"),
                ),
            ),
            Heading("History"),
            Para(
                "Mrs. Brooks is a 31-year-old woman in her second pregnancy. Her first pregnancy "
                "ended in an uncomplicated term vaginal delivery in 2022; the baby weighed 4.2 kg. "
                "**No history of pre-eclampsia, gestational hypertension or "
                "stillbirth.** No chronic medical conditions."
            ),
            Para(
                f"The estimated delivery date is {fmt_date(EDD)}, calculated from the last "
                "menstrual period and confirmed by the dating scan."
            ),
            TwoColumns(
                left=(
                    Heading("Allergies"),
                    Bullets(
                        (
                            "Latex: contact dermatitis",
                            "No known drug allergies",
                        )
                    ),
                ),
                right=(
                    Heading("Medications"),
                    Bullets(
                        (
                            "Folic acid 400 mcg once daily",
                            "Vitamin D 1000 IU once daily",
                        )
                    ),
                ),
            ),
            Heading("Obstetric History"),
            DataTable(
                ("Pregnancy", "Year", "Outcome", "Birth weight", "Complications"),
                (
                    ("1", "2022", "Term vaginal delivery, live girl", "4.2 kg", "None"),
                    ("2", "2026", "Current pregnancy", "-", "-"),
                ),
                widths=(1.0, 0.8, 3.0, 1.2, 1.6),
            ),
            Heading("Family and Social History"),
            Bullets(
                (
                    "Mother has type 2 diabetes diagnosed at age 58.",
                    "Works as a primary school teacher; does not smoke or drink alcohol.",
                    "Lives with her husband and daughter; good family support.",
                )
            ),
            Heading("Screening Offered at Booking"),
            DataTable(
                ("Test", "Timing", "Decision"),
                (
                    ("Dating ultrasound", "8 to 12 weeks", "Accepted"),
                    ("Combined first-trimester screening", "11 to 13 weeks", "Accepted"),
                    ("Anomaly ultrasound", "18 to 20 weeks", "Accepted"),
                    ("75 g glucose tolerance test", "24 to 28 weeks", "Accepted"),
                ),
                widths=(3.0, 1.8, 1.8),
            ),
            Heading("Risk Assessment"),
            Para(
                "A previous baby above 4 kg is a risk factor for gestational diabetes, so a "
                "75 g oral glucose tolerance test (OGTT) is planned at 24 to 28 weeks. Low risk "
                "for pre-eclampsia; aspirin not indicated."
            ),
            Heading("Plan"),
            Bullets(
                (
                    "Booking bloods and urine culture today.",
                    "Anomaly scan at 18 to 20 weeks; growth scans from 28 weeks.",
                    "OGTT at 24 to 28 weeks.",
                    "Next visit at 16 weeks.",
                )
            ),
        ),
    )


def _booking_labs() -> ReportSpec:
    return ReportSpec(
        file="lab_report_2026-06-02.pdf",
        name="Antenatal Booking Bloods - Jun 2026",
        category="lab",
        notes="Booking blood tests: blood count, ferritin, blood group, infection screen, HbA1c.",
        day=date(2026, 6, 2),
        title="Laboratory Report",
        department=DEPT_LAB,
        author="Dr. Marcus Lee, Consultant Biochemist",
        blocks=(
            Grid(
                (
                    ("Collected", "02 Jun 2026 09:25"),
                    ("Gestation", gestation(LMP, date(2026, 6, 2))),
                    ("Specimen", "Serum, EDTA whole blood, urine"),
                )
            ),
            Heading("Haematology"),
            LabTable(
                (
                    LabResult("Haemoglobin", 12.9, "g/dL", 11.0, 14.0),
                    LabResult("Mean cell volume", 88, "fL", 80, 100, 0),
                    LabResult("Platelets", 262, "10^9/L", 150, 400, 0),
                    LabResult("Ferritin", 38, "ug/L", 15, 150, 0),
                )
            ),
            Heading("Glycaemia and Thyroid"),
            LabTable(
                (
                    HBA1C,
                    LabResult("TSH", 1.8, "mIU/L", 0.1, 2.5),
                )
            ),
            Heading("Blood Group and Antibodies"),
            LabTable(
                (
                    LabResult("ABO and Rh(D) group", "O positive"),
                    LabResult("Red cell antibody screen", "Negative"),
                )
            ),
            Heading("Infection Screen"),
            LabTable(
                (
                    LabResult("Rubella IgG", "Immune"),
                    LabResult("Hepatitis B surface antigen", "Non-reactive"),
                    LabResult("HIV 1/2 antibody and antigen", "Non-reactive"),
                    LabResult("Syphilis serology", "Non-reactive"),
                    LabResult("Urine culture", "No growth"),
                )
            ),
        ),
    )


def _ogtt_labs() -> ReportSpec:
    day = date(2026, 9, 16)
    return ReportSpec(
        file="lab_report_2026-09-16.pdf",
        name="Glucose Tolerance Test and Iron Studies - Sep 2026",
        category="lab",
        notes="75 g OGTT at 24 weeks with repeat blood count and ferritin.",
        day=day,
        title="Laboratory Report",
        department=DEPT_LAB,
        author="Dr. Marcus Lee, Consultant Biochemist",
        blocks=(
            Grid(
                (
                    ("Collected", "16 Sep 2026 08:15"),
                    ("Gestation", gestation(LMP, day)),
                    ("Fasting status", "Fasting, 10 hours"),
                )
            ),
            Heading("75 g Oral Glucose Tolerance Test"),
            LabTable((OGTT_FASTING, OGTT_1H, OGTT_2H)),
            Para(
                "Diagnostic thresholds in pregnancy: fasting 92 mg/dL, 1 hour 180 mg/dL, "
                "2 hour 153 mg/dL. All three values are at or above the threshold, which meets "
                "the criteria for gestational diabetes mellitus (GDM)."
            ),
            Heading("Haematology and Iron Studies"),
            LabTable(
                (
                    LabResult("Haemoglobin", 11.2, "g/dL", 10.5, 14.0),
                    FERRITIN_SEP,
                )
            ),
            Heading("Interpretation"),
            Para(
                "Low ferritin indicates iron deficiency without anaemia. Oral iron "
                "(ferrous sulfate 200 mg once daily) is recommended."
            ),
        ),
    )


def _scan() -> ReportSpec:
    day = date(2026, 10, 13)
    return ReportSpec(
        file="obstetric_ultrasound_report_2026-10-13.pdf",
        name="Obstetric Growth Scan - Oct 2026",
        category="imaging",
        notes="Third-trimester growth scan with biometry, liquor volume and placental position.",
        day=day,
        title="Obstetric Ultrasound Report - Growth Scan",
        department=DEPT_IMAGING,
        author="Dr. Yusuf Rahman, Consultant in Fetal Medicine",
        blocks=(
            Grid(
                (
                    ("Gestation", gestation(LMP, day)),
                    ("Indication", "Growth scan; gestational diabetes"),
                    ("Previous scan", "Anomaly scan 12 Aug 2026, no structural abnormality"),
                )
            ),
            Heading("Fetal Biometry"),
            DataTable(
                ("Parameter", "Measurement", "Centile"),
                (
                    ("Biparietal diameter (BPD)", "71 mm", "52nd"),
                    ("Head circumference (HC)", "262 mm", "50th"),
                    ("Abdominal circumference (AC)", "241 mm", "56th"),
                    ("Femur length (FL)", "53 mm", "48th"),
                    ("Estimated fetal weight (EFW)", "1180 g", "54th"),
                ),
                widths=(3.0, 1.8, 1.4),
            ),
            Heading("Fetal Anatomy Review"),
            DataTable(
                ("Structure", "Assessment"),
                (
                    ("Head and brain", "Normal ventricles, midline structures and cerebellum"),
                    ("Face and spine", "Normal profile; spine intact in sagittal view"),
                    ("Heart", "Four-chamber view and outflow tracts normal"),
                    ("Abdomen", "Stomach bubble present; kidneys and bladder normal"),
                    ("Limbs", "Four limbs seen with normal long bones"),
                ),
                widths=(1.8, 5.0),
            ),
            Heading("Findings"),
            Bullets(
                (
                    "Single live fetus in cephalic presentation. Fetal heart rate 144 /min.",
                    "Amniotic fluid index 14.2 cm, normal.",
                    "Placenta anterior and fundal; no placenta praevia.",
                    "Umbilical artery Doppler: normal waveform and resistance index.",
                )
            ),
            Heading("Impression"),
            Para("Appropriate fetal growth with normal liquor volume. No features of macrosomia."),
        ),
    )


def _followup() -> ReportSpec:
    day = date(2026, 10, 27)
    return ReportSpec(
        file="antenatal_consultation_2026-10-27.pdf",
        name="Antenatal Review - Oct 2026",
        category="consultation",
        notes="Gestational diabetes and iron deficiency follow-up with current medication.",
        day=day,
        title="Antenatal Consultation",
        department=DEPT_OBS,
        author="Dr. Laura Whitcombe, Consultant Obstetrician",
        blocks=(
            Grid(
                (
                    ("Gestation", gestation(LMP, day)),
                    ("Blood pressure", "116/70 mmHg"),
                    ("Fundal height", "30 cm"),
                )
            ),
            Heading("Gestational Diabetes"),
            Para(
                "GDM was diagnosed on the 75 g OGTT of 16 Sep 2026 and is managed with diet. The "
                "glucose diary shows fasting readings of 86 to 96 mg/dL and one-hour post-meal "
                "readings of 118 to 152 mg/dL, within the targets of 95 and 140 mg/dL for fasting "
                "and post-meal respectively in most readings. Insulin is not required at present."
            ),
            Heading("Current Medications"),
            DataTable(
                ("Medicine", "Dose", "Frequency", "Change"),
                (
                    (
                        "Ferrous sulfate",
                        "200 mg",
                        "Twice daily (BD)",
                        "Increased from once daily (started 16 Sep 2026) on 27 Oct 2026.",
                    ),
                    ("Vitamin D", "1000 IU", "Once daily", "Unchanged."),
                    ("Folic acid", "-", "-", "Stopped after 12 weeks of pregnancy."),
                ),
                widths=(1.6, 1.0, 1.6, 3.4),
            ),
            Heading("Plan"),
            Bullets(
                (
                    "Continue diet control and four-times-daily glucose checks.",
                    "Repeat growth scan at 36 weeks.",
                    "Antenatal visits every two weeks; plan delivery discussion at 36 weeks.",
                )
            ),
        ),
    )


def _facts() -> dict[str, Fact]:
    ogtt = "lab_report_2026-09-16.pdf"
    return {
        "ogtt": Fact(ogtt, (OGTT_FASTING.needle, OGTT_1H.needle, OGTT_2H.needle)),
        "edd": Fact(
            "antenatal_booking_visit_2026-06-02.pdf",
            (f"The estimated delivery date is {fmt_date(EDD)}",),
        ),
        "iron_now": Fact(
            "antenatal_consultation_2026-10-27.pdf",
            ("Ferrous sulfate 200 mg Twice daily (BD) Increased from once daily",),
        ),
        "efw": Fact(
            "obstetric_ultrasound_report_2026-10-13.pdf", ("Estimated fetal weight (EFW) 1180 g",)
        ),
        "gdm": Fact(ogtt, ("meets the criteria for gestational diabetes mellitus (GDM)",)),
        "no_preeclampsia": Fact(
            "antenatal_booking_visit_2026-06-02.pdf",
            ("No history of pre-eclampsia, gestational hypertension or stillbirth",),
        ),
        "hba1c": Fact("lab_report_2026-06-02.pdf", (HBA1C.needle,)),
        "presentation": Fact(
            "obstetric_ultrasound_report_2026-10-13.pdf",
            ("Single live fetus in cephalic presentation",),
        ),
    }


def _questions() -> tuple[QuestionSpec, ...]:
    return (
        QuestionSpec(
            "table",
            "What were the fasting, 1-hour and 2-hour values on the glucose tolerance test?",
            facts=("ogtt",),
            must_include=(number_re("98"), number_re("182"), number_re("158")),
        ),
        QuestionSpec(
            "temporal",
            "What is the patient's expected delivery date?",
            facts=("edd",),
            must_include=(date_re(EDD),),
        ),
        QuestionSpec(
            "temporal",
            "What is the current dose of ferrous sulfate?",
            facts=("iron_now",),
            must_include=(r"200\s*mg", r"twice|BD|two times|2 times"),
        ),
        QuestionSpec(
            "numeric",
            "What was the estimated fetal weight on the latest growth scan?",
            facts=("efw",),
            must_include=(number_re("1180"),),
        ),
        QuestionSpec(
            "abbreviation",
            "Does the patient have diabetes in pregnancy?",
            facts=("gdm",),
            must_include=(r"gestational diabetes|GDM",),
        ),
        QuestionSpec(
            "negation",
            "Is there any history of pre-eclampsia?",
            facts=("no_preeclampsia",),
            must_include=(r"\b(?:no|not|none|without|never)\b",),
            must_not_include=(NEGATIVE_START_RE,),
        ),
        QuestionSpec(
            "cross_patient",
            "What is the patient's HbA1c?",
            facts=("hba1c",),
            must_include=(number_re("5.1"),),
            must_not_include=(number_re("8.6", "7.9", "7.2"),),
        ),
        QuestionSpec(
            "factoid",
            "In which position is the baby lying?",
            facts=("presentation",),
            must_include=(r"cephalic|head[- ]down",),
        ),
    )


def build() -> PatientSpec:
    return PatientSpec(
        uhid=UHID,
        name="Hannah Brooks",
        age=31,
        gender="female",
        summary="Second pregnancy with gestational diabetes and iron deficiency, due January 2027.",
        reports=(_booking(), _booking_labs(), _ogtt_labs(), _scan(), _followup()),
        facts=_facts(),
        questions=_questions(),
    )
