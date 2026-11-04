"""MG25004 - right total knee replacement (TKR) and recovery.

Planted cases: a fact that spans a page break (staple removal), an anticoagulant dose and
duration present only in a table cell, range-of-movement progress across two reports, and
negated comorbidities.
"""

from datetime import date, timedelta

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
    Turn,
    TwoColumns,
    date_re,
    dose_re,
    fmt_date,
    number_re,
)

UHID = "MG25004"
DEPT_ORTHO = "Department of Orthopaedic Surgery"
DEPT_RADIOLOGY = "Department of Radiology"

SURGERY_DAY = date(2026, 4, 6)
DISCHARGE_DAY = date(2026, 4, 10)
STAPLE_REMOVAL_DAY = SURGERY_DAY + timedelta(days=14)


def _preop_xray() -> ReportSpec:
    return ReportSpec(
        file="knee_xray_report_2026-03-20.pdf",
        name="Right Knee X-ray - Mar 2026",
        category="imaging",
        notes="Pre-operative weight-bearing radiographs of both knees.",
        day=date(2026, 3, 20),
        title="Radiology Report - Knee X-ray (Weight-bearing)",
        department=DEPT_RADIOLOGY,
        author="Dr. Nikhil Bhatt, Consultant Radiologist",
        blocks=(
            Grid(
                (
                    ("Examination", "Both knees, standing AP and lateral"),
                    ("Clinical indication", "Right knee pain, pre-operative assessment"),
                    ("Comparison", "None"),
                )
            ),
            Heading("Findings"),
            Heading("Right Knee"),
            Bullets(
                (
                    "Severe tricompartmental osteoarthritis, worst in the medial compartment: "
                    "**Kellgren-Lawrence grade 4**.",
                    "Near-complete loss of medial joint space with bone-on-bone contact.",
                    "Marginal osteophytes and subchondral sclerosis.",
                    "Varus deformity of 8 degrees.",
                    "No fracture or lytic lesion.",
                )
            ),
            Heading("Left Knee"),
            Para("Mild degenerative change, Kellgren-Lawrence grade 2. Joint space preserved."),
            Heading("Impression"),
            Para(
                "Advanced right knee osteoarthritis suitable for arthroplasty. "
                "Mild left knee osteoarthritis."
            ),
        ),
    )


def _discharge() -> ReportSpec:
    return ReportSpec(
        file="discharge_summary_2026-04-10.pdf",
        name="Discharge Summary - Apr 2026",
        category="discharge",
        notes="Right total knee replacement; recovery and discharge medication.",
        day=DISCHARGE_DAY,
        title="Discharge Summary",
        department=DEPT_ORTHO,
        author="Mr. David Okoye, Consultant Orthopaedic Surgeon",
        blocks=(
            Grid(
                (
                    ("Admitted", "05 Apr 2026"),
                    ("Surgery", fmt_date(SURGERY_DAY)),
                    ("Discharged", fmt_date(DISCHARGE_DAY)),
                )
            ),
            Heading("Diagnosis and Procedure"),
            Bullets(
                (
                    "Severe osteoarthritis of the right knee",
                    f"Right total knee replacement (TKR), cemented, performed on "
                    f"{fmt_date(SURGERY_DAY)} under spinal anaesthesia with an adductor "
                    "canal block",
                )
            ),
            TwoColumns(
                left=(
                    Heading("Past Medical History"),
                    Bullets(
                        (
                            "Hypertension, treated with losartan",
                            "No history of diabetes mellitus or cardiac disease",
                            "Appendicectomy 1985",
                        )
                    ),
                ),
                right=(
                    Heading("Allergies"),
                    Para("No known drug allergies."),
                ),
            ),
            Heading("Blood Results"),
            LabTable(
                (
                    LabResult("Haemoglobin, pre-operative", 11.4, "g/dL", 12.0, 15.5),
                    LabResult("Haemoglobin, post-operative day 1", 10.1, "g/dL", 12.0, 15.5),
                )
            ),
            Heading("Hospital Course"),
            Para(
                "The operation was uncomplicated with a tourniquet time of 74 minutes. She was "
                "mobilised with a physiotherapist on the first post-operative day and progressed "
                "from a walking frame to elbow crutches. No blood transfusion was required. Knee "
                "flexion at discharge was 70 degrees."
            ),
            Heading("Operative Details"),
            DataTable(
                ("Item", "Detail"),
                (
                    ("Surgeon", "Mr. David Okoye (fictional)"),
                    (
                        "Implant",
                        "Cemented posterior-stabilised total knee prosthesis, size 3",
                    ),
                    ("Anaesthesia", "Spinal anaesthesia with adductor canal block"),
                    ("Tourniquet time", "74 minutes"),
                    ("Estimated blood loss", "250 mL"),
                    ("Tranexamic acid", "1 g intravenously at induction"),
                    ("Wound closure", "Layered closure with skin staples"),
                    (
                        "Antibiotic prophylaxis",
                        "Cefazolin 2 g intravenously at induction, two further doses over 24 hours",
                    ),
                ),
                widths=(1.8, 5.0),
            ),
            Heading("Wound Care"),
            Para(
                "The wound is clean, dry and intact with a waterproof dressing in place. "
                "Please keep the dressing dry and do not apply creams or ointments to the scar. "
                f"Skin staples are to be removed on post-operative day 14 "
                f"({fmt_date(STAPLE_REMOVAL_DAY)}) at the wound clinic, provided the wound has "
                "healed and there is no discharge or spreading redness. If the wound is slow to "
                "heal, the staples remain in place and the review is repeated weekly."
            ),
            Heading("Recovery by Day"),
            DataTable(
                ("Day", "Date", "Mobility", "Pain score (0-10)"),
                (
                    ("1", "07 Apr 2026", "Sat out of bed; stood with frame", "4"),
                    ("2", "08 Apr 2026", "Walked 10 metres with frame and physiotherapist", "3"),
                    ("3", "09 Apr 2026", "Walked on ward; practised stairs", "3"),
                    ("4", "10 Apr 2026", "Independent with elbow crutches; discharged", "2"),
                ),
                widths=(0.6, 1.4, 4.0, 1.4),
            ),
            Heading("Medications on Discharge"),
            DataTable(
                ("Medicine", "Dose", "Frequency", "Duration", "Purpose"),
                (
                    (
                        "Enoxaparin",
                        "40 mg subcutaneous",
                        "Once daily",
                        "14 days",
                        "Prevention of venous thromboembolism",
                    ),
                    ("Paracetamol", "1 g", "Four times daily (QDS)", "Ongoing", "Analgesia"),
                    ("Tramadol", "50 mg", "Twice daily (BD)", "2 weeks", "Breakthrough pain"),
                    ("Lactulose", "15 mL", "Once daily", "While on tramadol", "Constipation"),
                    ("Losartan", "50 mg", "Once daily", "Ongoing", "Hypertension"),
                ),
                widths=(1.5, 1.6, 1.8, 1.4, 2.4),
            ),
            Heading("Follow-up"),
            Bullets(
                (
                    "Wound clinic on post-operative day 14 for staple removal.",
                    "Orthopaedic clinic at 6 weeks with knee radiographs.",
                    "Outpatient physiotherapy three times a week from discharge.",
                    "Contact the ward for calf pain or swelling, fever or wound discharge.",
                )
            ),
        ),
    )


def _postop_xray() -> ReportSpec:
    return ReportSpec(
        file="post_op_xray_report_2026-04-07.pdf",
        name="Post-operative Knee X-ray - Apr 2026",
        category="imaging",
        notes="Right knee radiographs on the first day after total knee replacement.",
        day=date(2026, 4, 7),
        title="Radiology Report - Right Knee X-ray (Post-operative)",
        department=DEPT_RADIOLOGY,
        author="Dr. Nikhil Bhatt, Consultant Radiologist",
        blocks=(
            Grid(
                (
                    ("Examination", "Right knee, AP and lateral"),
                    ("Clinical indication", "Post-operative day 1, total knee replacement"),
                    ("Comparison", "Knee X-ray 20 Mar 2026"),
                )
            ),
            Heading("Findings"),
            Bullets(
                (
                    "Cemented total knee prosthesis is well-positioned with satisfactory "
                    "alignment.",
                    "No periprosthetic fracture or lucent line.",
                    "Skin staples and a small joint effusion in keeping with recent surgery.",
                )
            ),
            Heading("Impression"),
            Para("Satisfactory post-operative appearance of a right total knee replacement."),
        ),
    )


def _followup() -> ReportSpec:
    return ReportSpec(
        file="orthopaedic_followup_2026-05-18.pdf",
        name="Orthopaedic Follow-up - May 2026",
        category="consultation",
        notes="Six-week review after total knee replacement with range-of-movement progress.",
        day=date(2026, 5, 18),
        title="Orthopaedic Outpatient Consultation",
        department=DEPT_ORTHO,
        author="Mr. David Okoye, Consultant Orthopaedic Surgeon",
        blocks=(
            Heading("Reason for Visit"),
            Para(
                "Six-week review following right total knee replacement on "
                f"{fmt_date(SURGERY_DAY)}. She is pleased with her progress and walks "
                "without discomfort for about 30 minutes."
            ),
            Heading("Examination"),
            Para(
                "Wound fully healed with a well-formed scar. **No signs of infection**: no "
                "warmth, erythema or discharge. **No calf swelling or tenderness.** The knee has "
                "a small residual effusion."
            ),
            Heading("Range of Movement"),
            DataTable(
                ("Date", "Time since surgery", "Flexion", "Extension lag", "Walking aid"),
                (
                    ("10 Apr 2026 (discharge)", "4 days", "70°", "10°", "Walking frame"),
                    ("20 Apr 2026 (wound clinic)", "14 days", "85°", "5°", "Elbow crutches"),
                    ("18 May 2026 (this visit)", "6 weeks", "105°", "0°", "Single stick"),
                ),
                widths=(2.4, 1.6, 1.0, 1.3, 1.7),
            ),
            Heading("Medications"),
            DataTable(
                ("Medicine", "Dose", "Frequency", "Status"),
                (
                    ("Tramadol", "-", "-", "Stopped at 2 weeks"),
                    ("Paracetamol", "1 g", "As needed, maximum four times daily", "Continue"),
                    ("Losartan", "50 mg", "Once daily", "Continue"),
                ),
                widths=(1.8, 1.0, 3.0, 1.8),
            ),
            Heading("Plan"),
            Bullets(
                (
                    "Outpatient physiotherapy three times a week; target flexion 120 degrees.",
                    "Knee radiograph and clinic review at 6 months after surgery.",
                    "Antibiotic prophylaxis before dental procedures is not required routinely.",
                )
            ),
        ),
    )


def _facts() -> dict[str, Fact]:
    discharge = "discharge_summary_2026-04-10.pdf"
    followup = "orthopaedic_followup_2026-05-18.pdf"
    return {
        "enoxaparin": Fact(discharge, ("Enoxaparin 40 mg subcutaneous Once daily 14 days",)),
        "rom_discharge": Fact(followup, ("10 Apr 2026 (discharge) 4 days 70°",)),
        "rom_six_weeks": Fact(followup, ("18 May 2026 (this visit) 6 weeks 105°",)),
        "rom_two_weeks": Fact(followup, ("20 Apr 2026 (wound clinic) 14 days 85°",)),
        "tkr_date": Fact(
            discharge,
            (f"TKR), cemented, performed on {fmt_date(SURGERY_DAY)}",),
        ),
        "no_diabetes": Fact(discharge, ("No history of diabetes mellitus or cardiac disease",)),
        "implant_position": Fact(
            "post_op_xray_report_2026-04-07.pdf",
            ("Cemented total knee prosthesis is well-positioned",),
        ),
        "kl_grade": Fact("knee_xray_report_2026-03-20.pdf", ("Kellgren-Lawrence grade 4",)),
        "staples": Fact(
            discharge,
            (
                f"post-operative day 14 ({fmt_date(STAPLE_REMOVAL_DAY)})",
                "repeated weekly.",
            ),
            spans_page_break=True,
        ),
    }


def _questions() -> tuple[QuestionSpec, ...]:
    return (
        QuestionSpec(
            "table",
            "What dose and duration of enoxaparin was prescribed after surgery?",
            facts=("enoxaparin",),
            must_include=(dose_re("40"), r"14\s*days"),
        ),
        QuestionSpec(
            "multi_chunk",
            "How has the patient's knee flexion improved since surgery?",
            facts=("rom_discharge", "rom_two_weeks", "rom_six_weeks"),
            must_include=(number_re("70"), number_re("85"), number_re("105")),
        ),
        QuestionSpec(
            "abbreviation",
            "When was the patient's TKR performed?",
            facts=("tkr_date",),
            must_include=(date_re(SURGERY_DAY),),
        ),
        QuestionSpec(
            "negation",
            "Does the patient have diabetes?",
            facts=("no_diabetes",),
            must_include=(r"\b(?:no|not|none|without|never)\b",),
            must_not_include=(NEGATIVE_START_RE,),
        ),
        QuestionSpec(
            "factoid",
            "Was the implant well placed on the first post-operative X-ray?",
            facts=("implant_position",),
            must_include=(
                r"well[\s-]*positioned|satisfactory",
                r"no\s+periprosthetic\s+fracture|fracture",
            ),
        ),
        QuestionSpec(
            "numeric",
            "What Kellgren-Lawrence grade was the right knee osteoarthritis before surgery?",
            facts=("kl_grade",),
            must_include=(r"\b(?:grade\s*)?4\b",),
        ),
        QuestionSpec(
            "multi_chunk",
            "When should the staples be removed, and what if the wound is slow to heal?",
            facts=("staples",),
            must_include=(
                r"day\s*14|14\s*days|two weeks|2 weeks",
                date_re(STAPLE_REMOVAL_DAY),
                r"remain|weekly|repeated",
            ),
        ),
        QuestionSpec(
            "followup",
            "And what was it at discharge?",
            facts=("rom_discharge",),
            must_include=(number_re("70"),),
            history=(
                Turn("user", "How far can the patient bend the knee now?"),
                Turn(
                    "assistant",
                    "At the 6-week review on 18 May 2026 knee flexion was 105 degrees [C1].",
                ),
            ),
        ),
    )


def build() -> PatientSpec:
    return PatientSpec(
        uhid=UHID,
        name="Priya Nair",
        age=67,
        gender="female",
        summary="Right total knee replacement for osteoarthritis, six weeks into rehabilitation.",
        reports=(_preop_xray(), _postop_xray(), _discharge(), _followup()),
        facts=_facts(),
        questions=_questions(),
    )
