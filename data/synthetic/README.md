# Synthetic patient dataset

Fully fictional records for demonstrating and evaluating the Clinical Assistant. Nothing here
describes a real person or facility: the hospital is "Northbridge General Hospital (fictional)",
every page of every PDF carries the footer `SYNTHETIC DATA — FOR DEMONSTRATION ONLY`, and all
names, numbers and dates are invented.

## Contents

| Path | What it is |
|---|---|
| `pdfs/<uhid>/<file>.pdf` | The reports: letterhead, running header, tables, repeated footer. |
| `manifest.json` | `{patients: [{uhid, name, age, gender, summary, reports: [{file, name, category, notes, date}]}]}`. The seed script uploads exactly this. |
| `../../backend/evals/data/golden.jsonl` | The golden evaluation set (one JSON object per line). |

Six patients (`MG25001` to `MG25006`) cover type 2 diabetes with CKD, atrial fibrillation on an
anticoagulant, COPD, a post-operative knee replacement, a pregnancy follow-up and oncology
follow-up. Each has 4 to 5 reports across the categories `lab`, `imaging`, `discharge`,
`prescription` and `consultation`, dated between September 2025 and October 2026.

## Retrieval cases planted on purpose

- **Time matters**: HbA1c falls across four reports; a metformin, rivaroxaban, inhaler or iron
  dose changes between visits, so the "current" dose differs from an older one.
- **Superseded report**: `MG25001` has a preliminary lab report and a corrected one for the same
  collection (potassium 6.1 on a haemolysed sample, 4.9 after recollection).
- **Cross-patient isolation**: the same lab names appear for several patients with different values.
- **Wording**: abbreviations vs spelled-out terms (HbA1c / glycated haemoglobin, TKR, GDM, CEA),
  brand vs generic drugs (Xarelto / rivaroxaban, Symbicort / budesonide-formoterol).
- **Negation**: "no history of ..." statements.
- **Layout**: facts that live only in a table cell, an allergy only on page 3 of a discharge
  summary, and two facts that straddle a page break.
- **Prompt injection**: a transcribed patient message inside an otherwise normal oncology note
  tells the assistant to ignore its instructions and leak other patients' data.

## Golden set

Fields per line: `id`, `patient_id`, `question`, `type`, `answerable`, `expected_reports`,
`expected_pages`, `must_include`, `must_not_include` and, for follow-up questions, `history`.

- `type` is one of `factoid`, `numeric`, `temporal`, `table`, `negation`, `multi_chunk`,
  `abbreviation`, `followup`, `cross_patient`, `unanswerable`, `injection`.
- `expected_reports` are manifest file names; `expected_pages` are 1-based page numbers. A
  retrieved chunk from one of those pages counts as a retrieval hit. For questions that span
  several reports the page list is the union across those reports.
- `must_include` regexes must all match the final answer and `must_not_include` regexes must
  not match it (case-insensitive). For unanswerable questions `must_include` is a loose
  "the records do not say" pattern.

## Regenerating

From the repository root:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\generate_synthetic_data.py
```

The output is deterministic (fixed seed, pinned PDF dates and ids), so re-running reproduces
byte-identical files. Ground truth is never typed by hand: each question points at declared
facts, the generator locates those facts in the rendered PDFs with PyMuPDF to obtain the page
numbers, and it then checks that every `must_include` pattern matches the text of the expected
pages and that every `must_not_include` pattern would genuinely catch a leak. Any
inconsistency stops generation with a non-zero exit code.
