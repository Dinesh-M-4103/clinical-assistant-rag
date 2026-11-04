"""MG25003 - COPD (formerly labelled asthma) with an exacerbation admission.

Planted cases: a penicillin allergy that appears only on page 3 of the discharge summary,
an inhaler dose that doubles between visits (brand 'Symbicort' vs generic budesonide/formoterol),
facts inside tables, and negations ('no history of tuberculosis').
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
    NewPage,
    Para,
    PatientSpec,
    QuestionSpec,
    ReportSpec,
    TwoColumns,
    number_re,
)

UHID = "MG25003"
DEPT_RESP = "Department of Respiratory Medicine"
DEPT_RADIOLOGY = "Department of Radiology"


def _consultation() -> ReportSpec:
    return ReportSpec(
        file="pulmonology_consultation_2025-11-04.pdf",
        name="Pulmonology Consultation - Nov 2025",
        category="consultation",
        notes="COPD assessment with spirometry and inhaler regimen.",
        day=date(2025, 11, 4),
        title="Respiratory Outpatient Consultation",
        department=DEPT_RESP,
        author="Dr. Fiona Gallagher, Consultant Respiratory Physician",
        blocks=(
            Heading("Reason for Visit"),
            Para(
                "Annual review of chronic obstructive pulmonary disease (COPD). Mr. Okafor was "
                "diagnosed with asthma in childhood; the diagnosis was revised to COPD in 2023 "
                "after persistent airflow obstruction was documented."
            ),
            Heading("History"),
            Para(
                "Exertional breathlessness (mMRC grade 2) and a morning cough with small amounts "
                "of white sputum. One exacerbation treated in primary care in the last 12 "
                "months. COPD Assessment Test (CAT) score 18."
            ),
            TwoColumns(
                left=(
                    Heading("Smoking and Exposure"),
                    Bullets(
                        (
                            "Ex-smoker, 30 pack-years, quit in 2019",
                            "Worked in a printing firm; no known dust exposure",
                            "No history of tuberculosis",
                        )
                    ),
                ),
                right=(
                    Heading("Examination"),
                    Bullets(
                        (
                            "SpO2 94% on room air",
                            "Respiratory rate 18 /min",
                            "Prolonged expiration, scattered wheeze",
                            "No clubbing or peripheral oedema",
                        )
                    ),
                ),
            ),
            Heading("Spirometry (post-bronchodilator)"),
            DataTable(
                ("Parameter", "Measured", "Predicted", "% Predicted"),
                (
                    ("FEV1", "1.62 L", "3.12 L", "52 %"),
                    ("FVC", "3.10 L", "4.05 L", "77 %"),
                    ("FEV1/FVC ratio", "0.52", "-", "-"),
                ),
                widths=(2.2, 1.6, 1.6, 1.6),
            ),
            Para(
                "Persistent airflow limitation (FEV1/FVC below 0.70 after bronchodilator): "
                "**GOLD grade 2 (moderate)**."
            ),
            Heading("Current Medications"),
            DataTable(
                ("Medicine", "Brand", "Dose", "Frequency"),
                (
                    ("Tiotropium", "Spiriva", "18 mcg capsule inhaled", "Once daily"),
                    ("Salbutamol", "Ventolin", "100 mcg/puff, 2 puffs", "As needed (PRN)"),
                ),
                widths=(1.8, 1.4, 2.4, 1.8),
            ),
            Heading("Plan"),
            Bullets(
                (
                    "Continue tiotropium; check inhaler technique at each visit.",
                    "Influenza and pneumococcal vaccination up to date.",
                    "Chest X-ray and repeat spirometry in 6 months.",
                    "Offer pulmonary rehabilitation referral.",
                )
            ),
        ),
    )


def _chest_xray() -> ReportSpec:
    return ReportSpec(
        file="chest_xray_report_2026-05-12.pdf",
        name="Chest X-ray - May 2026",
        category="imaging",
        notes="PA and lateral chest radiograph.",
        day=date(2026, 5, 12),
        title="Radiology Report - Chest X-ray (PA and Lateral)",
        department=DEPT_RADIOLOGY,
        author="Dr. Nikhil Bhatt, Consultant Radiologist",
        blocks=(
            Grid(
                (
                    ("Examination", "Chest radiograph, PA and lateral"),
                    ("Clinical indication", "COPD, six-month review"),
                    ("Comparison", "None available"),
                ),
            ),
            Heading("Findings"),
            Bullets(
                (
                    "Lungs are hyperinflated with flattened hemidiaphragms and increased "
                    "retrosternal airspace.",
                    "No focal consolidation or mass lesion.",
                    "No pleural effusion or pneumothorax.",
                    "Heart size is normal. Mediastinal contours are unremarkable.",
                    "No acute bony abnormality.",
                )
            ),
            Heading("Impression"),
            Para("Hyperinflation in keeping with COPD. No acute cardiopulmonary abnormality."),
        ),
    )


def _prescription() -> ReportSpec:
    return ReportSpec(
        file="prescription_2026-05-20.pdf",
        name="Prescription - May 2026",
        category="prescription",
        notes="Inhaled therapy escalated after review of symptoms.",
        day=date(2026, 5, 20),
        title="Outpatient Prescription",
        department=DEPT_RESP,
        author="Dr. Fiona Gallagher, Consultant Respiratory Physician",
        blocks=(
            Grid(
                (
                    ("Diagnosis", "COPD, GOLD grade 2"),
                    ("Visit reason", "Increasing breathlessness"),
                    ("Inhaler technique", "Checked, satisfactory"),
                ),
            ),
            Heading("Medications"),
            DataTable(
                ("Medicine", "Strength", "Dose", "Frequency", "Remarks"),
                (
                    (
                        "Budesonide/formoterol (Symbicort)",
                        "160/4.5 mcg",
                        "1 puff",
                        "Twice daily (BD)",
                        "New. Rinse mouth after use.",
                    ),
                    ("Tiotropium (Spiriva)", "18 mcg", "1 capsule", "Once daily", "Continue."),
                    (
                        "Salbutamol (Ventolin)",
                        "100 mcg/puff",
                        "2 puffs",
                        "As needed (PRN)",
                        "Continue.",
                    ),
                ),
                widths=(2.6, 1.3, 1.0, 1.5, 2.2),
            ),
            Heading("Advice"),
            Bullets(
                (
                    "Use the reliever only when needed; seek review if it is needed more than "
                    "three times a week.",
                    "Review in 3 months or earlier if symptoms worsen.",
                )
            ),
        ),
    )


def _discharge() -> ReportSpec:
    admission_vitals = DataTable(
        ("Observation", "On admission", "At discharge"),
        (
            ("SpO2 (room air)", "88 %", "93 %"),
            ("Respiratory rate", "28 /min", "18 /min"),
            ("Heart rate", "112 /min", "84 /min"),
            ("Temperature", "37.9 C", "36.8 C"),
        ),
        widths=(2.4, 1.8, 1.8),
    )
    return ReportSpec(
        file="discharge_summary_2026-08-30.pdf",
        name="Discharge Summary - Aug 2026",
        category="discharge",
        notes="Admission for an acute exacerbation of COPD.",
        day=date(2026, 8, 30),
        title="Discharge Summary",
        department=DEPT_RESP,
        author="Dr. Fiona Gallagher, Consultant Respiratory Physician",
        blocks=(
            Grid(
                (
                    ("Admitted", "24 Aug 2026"),
                    ("Discharged", "30 Aug 2026"),
                    ("Ward", "Respiratory Ward 6A"),
                )
            ),
            Heading("Diagnosis"),
            Bullets(
                (
                    "Acute infective exacerbation of COPD (GOLD grade 2)",
                    "No ventilatory support required",
                )
            ),
            Heading("Presenting Complaint"),
            Para(
                "Five days of increasing breathlessness, cough and purulent sputum with fever. "
                "He was unable to speak in full sentences at home and was brought in by "
                "ambulance."
            ),
            Heading("Observations"),
            admission_vitals,
            Heading("Examination on Admission"),
            Bullets(
                (
                    "Using accessory muscles; speaking in short phrases.",
                    "Widespread expiratory wheeze with reduced air entry at both bases.",
                    "No peripheral oedema; jugular venous pressure not raised.",
                    "Alert and oriented; no flapping tremor.",
                )
            ),
            Heading("Investigations"),
            LabTable(
                (
                    "Blood tests on admission",
                    LabResult("Haemoglobin", 14.9, "g/dL", 13.0, 17.0),
                    LabResult("White cell count", 14.8, "10^9/L", 4.0, 11.0),
                    LabResult("C-reactive protein", 86, "mg/L", high=5, decimals=0),
                    "Arterial blood gas on room air",
                    LabResult("pH", 7.31, "", 7.35, 7.45, 2),
                    LabResult("PaCO2", 58, "mmHg", 35, 45, 0),
                    LabResult("PaO2", 54, "mmHg", 80, 100, 0),
                    LabResult("Bicarbonate", 29, "mmol/L", 22, 28, 0),
                )
            ),
            Heading("Microbiology and Imaging"),
            Para(
                "Sputum culture grew Haemophilus influenzae. Chest X-ray showed hyperinflation "
                "without consolidation. Renal function and electrolytes were normal."
            ),
            DataTable(
                ("Antibiotic", "Susceptibility"),
                (
                    ("Amoxicillin", "Sensitive"),
                    ("Doxycycline", "Sensitive"),
                    ("Clarithromycin", "Sensitive"),
                    ("Co-trimoxazole", "Resistant"),
                ),
                widths=(2.5, 2.0),
            ),
            Heading("Hospital Course"),
            Para(
                "He received nebulised salbutamol and ipratropium, controlled oxygen titrated to "
                "88-92 %, oral prednisolone 30 mg daily for 5 days and oral doxycycline 100 mg "
                "twice daily. Symptoms improved steadily and oxygen was weaned off on day 3."
            ),
            DataTable(
                ("Day", "Date", "Progress"),
                (
                    (
                        "1",
                        "24 Aug 2026",
                        "Admitted via emergency department; 4-hourly nebulisers, oxygen.",
                    ),
                    ("2", "25 Aug 2026", "Wheeze improving; started prednisolone and doxycycline."),
                    (
                        "3",
                        "26 Aug 2026",
                        "Oxygen weaned to room air; nebulisers reduced to 6-hourly.",
                    ),
                    (
                        "4",
                        "27 Aug 2026",
                        "Switched to inhalers; walking on the ward with a physiotherapist.",
                    ),
                    ("5", "28 Aug 2026", "Prednisolone course completed; sputum volume reduced."),
                    ("6", "30 Aug 2026", "Inhaler technique reviewed; discharged home."),
                ),
                widths=(0.6, 1.4, 5.0),
            ),
            NewPage(),
            Heading("Pharmacy Medication Reconciliation"),
            Para(
                "Completed by the ward pharmacist on 25 Aug 2026 from the patient's own account "
                "and his general practice record."
            ),
            Heading("Allergies and Adverse Drug Reactions"),
            Para("**Penicillin (amoxicillin): urticaria, 2012.** No other known allergies."),
            Heading("Medications on Discharge"),
            DataTable(
                ("Medicine", "Strength", "Dose", "Frequency", "Remarks"),
                (
                    (
                        "Budesonide/formoterol (Symbicort)",
                        "160/4.5 mcg",
                        "2 puffs",
                        "Twice daily (BD)",
                        "Increased from 1 puff twice daily.",
                    ),
                    ("Tiotropium (Spiriva)", "18 mcg", "1 capsule", "Once daily", "Unchanged."),
                    (
                        "Salbutamol (Ventolin)",
                        "100 mcg/puff",
                        "2 puffs",
                        "As needed (PRN)",
                        "Unchanged.",
                    ),
                    ("Doxycycline", "100 mg", "1 capsule", "Twice daily (BD)", "Completes 5 days."),
                    ("Prednisolone", "30 mg", "-", "-", "Course completed in hospital."),
                ),
                widths=(2.6, 1.3, 1.0, 1.5, 2.2),
            ),
            Heading("Social History and Smoking Status"),
            Para(
                "Ex-smoker; 30 pack-years; stopped smoking in 2019. Lives with his daughter. "
                "No alcohol excess."
            ),
            Heading("Follow-up"),
            Bullets(
                (
                    "Respiratory clinic in 6 weeks with repeat spirometry.",
                    "Pulmonary rehabilitation referral sent.",
                    "General practitioner review within 7 days of discharge.",
                    "Return if breathlessness worsens, sputum turns green or fever recurs.",
                )
            ),
            NewPage(),
            Heading("COPD Self-management Plan"),
            Para("Reviewed with Mr. Okafor and his daughter by the respiratory nurse specialist."),
            DataTable(
                ("Zone", "How you feel", "What to do"),
                (
                    (
                        "Green",
                        "Usual breathlessness and cough; sleeping well",
                        "Take regular inhalers; keep active; attend rehabilitation.",
                    ),
                    (
                        "Amber",
                        "More breathless, more sputum or sputum changes colour for two days",
                        "Use the reliever as needed and contact the general practice the same day.",
                    ),
                    (
                        "Red",
                        "Breathless at rest, confusion, blue lips or chest pain",
                        "Call the emergency services.",
                    ),
                ),
                widths=(1.0, 3.2, 3.8),
            ),
            Heading("Inhaler Technique Checklist"),
            Bullets(
                (
                    "Shake the inhaler, breathe out gently, then seal your lips on the mouthpiece.",
                    "Breathe in steadily while pressing once; hold your breath for 10 seconds.",
                    "Wait 30 seconds between puffs; rinse your mouth after the steroid inhaler.",
                    "Tiotropium capsule: pierce once, inhale twice from the same capsule.",
                )
            ),
            Heading("Vaccinations"),
            Para("Influenza vaccine given on 02 Oct 2025; pneumococcal vaccine given in 2024."),
        ),
    )


def _facts() -> dict[str, Fact]:
    consult = "pulmonology_consultation_2025-11-04.pdf"
    discharge = "discharge_summary_2026-08-30.pdf"
    return {
        "penicillin_allergy": Fact(discharge, ("Penicillin (amoxicillin): urticaria, 2012",)),
        "fev1": Fact(consult, ("FEV1 1.62 L 3.12 L 52 %",)),
        "gold": Fact(consult, ("GOLD grade 2 (moderate)",)),
        "symbicort_now": Fact(
            discharge,
            ("Budesonide/formoterol (Symbicort) 160/4.5 mcg 2 puffs Twice daily (BD)",),
        ),
        "no_tb": Fact(consult, ("No history of tuberculosis",)),
        "spo2_discharge": Fact(discharge, ("SpO2 (room air) 88 % 93 %",)),
        "smoking_consult": Fact(consult, ("Ex-smoker, 30 pack-years, quit in 2019",)),
        "smoking_discharge": Fact(
            discharge, ("Ex-smoker; 30 pack-years; stopped smoking in 2019",)
        ),
    }


def _questions() -> tuple[QuestionSpec, ...]:
    return (
        QuestionSpec(
            "factoid",
            "Is the patient allergic to any antibiotics?",
            facts=("penicillin_allergy",),
            must_include=(r"penicillin",),
        ),
        QuestionSpec(
            "numeric",
            "What was the patient's FEV1 and what percentage of predicted is it?",
            facts=("fev1",),
            must_include=(number_re("1.62"), r"52\s*%"),
        ),
        QuestionSpec(
            "abbreviation",
            "What severity grade of airflow limitation did the respiratory physician assign?",
            facts=("gold",),
            must_include=(r"GOLD\s*(?:grade\s*|stage\s*)?2|moderate",),
        ),
        QuestionSpec(
            "temporal",
            "What is the current dose of budesonide/formoterol?",
            facts=("symbicort_now",),
            must_include=(r"\b(?:2|two)\s*puffs",),
        ),
        QuestionSpec(
            "negation",
            "Has the patient ever had tuberculosis?",
            facts=("no_tb",),
            must_include=(r"\b(?:no|not|none|without|never)\b",),
            must_not_include=(NEGATIVE_START_RE,),
        ),
        QuestionSpec(
            "table",
            "What was the patient's oxygen saturation at discharge?",
            facts=("spo2_discharge",),
            must_include=(r"93\s*%",),
        ),
        QuestionSpec(
            "multi_chunk",
            "Summarise the patient's smoking history.",
            facts=("smoking_consult", "smoking_discharge"),
            must_include=(r"30[\s-]*pack", r"2019"),
        ),
        QuestionSpec(
            "cross_patient",
            "What is the patient's latest serum creatinine?",
            must_include=(REFUSAL_RE,),
            must_not_include=(number_re("1.9", "1.8", "1.3", "0.9"),),
            answerable=False,
        ),
    )


def build() -> PatientSpec:
    return PatientSpec(
        uhid=UHID,
        name="Daniel Okafor",
        age=58,
        gender="male",
        summary="COPD (GOLD grade 2, formerly labelled asthma); ex-smoker, recent exacerbation.",
        reports=(_consultation(), _chest_xray(), _prescription(), _discharge()),
        facts=_facts(),
        questions=_questions(),
    )
