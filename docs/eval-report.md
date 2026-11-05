# Evaluation report

How well does the pipeline find the right page of the right report? This report measures the
retrieval stage with real numbers and leaves the answer-quality section empty until the owner runs
it (it needs about 48 Gemini calls). Every number below is copied from
`backend/evals/results/latest.json`, the run `20261105-092158`. Nothing is rounded up.

Harness, commands and metric definitions: [`backend/evals/README.md`](../backend/evals/README.md).

## Methodology

- **System under test**: the real `RagPipeline` (no HTTP layer) with the shipped defaults:
  `BAAI/bge-small-en-v1.5` embeddings, ~300-token chunks with 50 overlap, dense top 20 and BM25 top
  20, RRF (k = 60), `cross-encoder/ms-marco-MiniLM-L-6-v2` reranking to the top 5, relevance gate at
  `MIN_RERANK_SCORE = 0.001`.
- **Corpus**: the synthetic records in `data/synthetic/`, ingested into a temporary Chroma store
  that is deleted after the run. Each patient has a separate collection, as in the app.
- **Ablation**: four retrieval modes share one embedder, reranker and store, so only the ranking
  changes: `dense` (vector search only), `bm25` (lexical only), `hybrid` (RRF of both) and
  `hybrid_rerank` (the default: hybrid plus the cross-encoder). Each mode returns its top 5.
- **Ground truth**: each golden question lists the expected report files and 1-based pages. A
  retrieved chunk is a hit when its (report, page) is one of them.
- **Metrics**: hit@1/3/5 (share of questions with a hit in the top k), MRR over the top 5, recall@k
  (share of expected reports with a hit in the top k), and mean retrieval latency per question
  (CPU, Windows 11, models already loaded).
- **No LLM was called.** Retrieval needs none, and the answer checks are regexes and page
  comparisons, never an LLM judge.
- **Reproducibility**: the retrieval stage is deterministic. The run was repeated before the final
  one and gave the same hit and MRR figures; only latency differs between runs.

## Dataset

52 hand-written questions over 6 fictional patients and 27 PDF reports (diabetes with CKD, atrial
fibrillation, COPD, knee replacement, pregnancy, oncology). The questions target the failure modes
of clinical RAG on purpose:

| Question type | Total | What it tests |
|---|---|---|
| temporal | 10 | "latest" or "current" values when older reports mention the same test or drug, including a preliminary and a corrected lab report |
| abbreviation | 7 | wording gaps: CKD vs chronic kidney disease, brand vs generic drug names |
| multi_chunk | 6 | answers that need several reports (a trend, a dose change) |
| negation | 6 | "no history of ..." statements |
| table | 5 | facts that only appear in a table cell or on a later page |
| numeric | 4 | exact figures |
| factoid | 4 | single plain facts |
| cross_patient | 4 | values that exist for another patient but not this one (2 are unanswerable) |
| followup | 2 | elliptical questions that depend on chat history |
| unanswerable | 2 | information that is not in the records |
| injection | 2 | a patient message inside a note tells the assistant to leak data |

48 questions have expected sources and are scored for retrieval. The other 4 are unanswerable by
design, so they feed the relevance-gate analysis instead. With only 48 scored questions, one
question moves a rate by 2.1 percentage points; read the differences between modes with that in
mind.

## Retrieval ablation

| Mode | Questions | hit@1 | hit@3 | hit@5 | MRR@5 | recall@1 | recall@3 | recall@5 | Mean latency (ms) |
|---|---|---|---|---|---|---|---|---|---|
| dense | 48 | 0.625 | 0.896 | 0.917 | 0.759 | 0.590 | 0.882 | 0.917 | 23 |
| bm25 | 48 | 0.667 | 0.896 | 0.938 | 0.777 | 0.622 | 0.875 | 0.931 | 1 |
| hybrid | 48 | 0.646 | 0.917 | 0.938 | 0.773 | 0.597 | 0.892 | 0.938 | 24 |
| hybrid_rerank | 48 | 0.688 | 0.875 | 0.958 | 0.793 | 0.649 | 0.851 | 0.941 | 1280 |

What the table says:

- **The default mode is best on hit@1, hit@5 and MRR**, but by a thin margin: hit@5 is 46/48 against
  45/48 for BM25 and hybrid and 44/48 for dense. hit@1 is 33/48 against 30/48 for dense.
- **Reranking is not a clear win.** It lifts hit@1 and hit@5 but lowers hit@3 (42/48 against 44/48
  for plain hybrid), and costs about 1.3 s per question on CPU against about 25 ms without it.
  Because the generator reads all 5 chunks, hit@5 matters most for answer quality, and that is
  where it leads.
- **BM25 is strong on this corpus.** Clinical text is full of exact tokens (drug names, test
  names, numbers), which favour lexical matching; BM25 alone beats dense at every cutoff.
- **Hybrid covers each side's blind spots**: dense missed the "most recent HbA1c" question (g01)
  and the diabetes-in-pregnancy question (g40) entirely, and BM25 missed the CKD-stage (g06) and
  baby-position (g43) questions. Hybrid recovered g01, g40 and g43 within its top 5; g06 stays
  missed by both BM25 and hybrid.

## Retrieval by question type

Each cell is `hit@1 / hit@5`.

| Question type | n | dense | bm25 | hybrid | hybrid_rerank |
|---|---|---|---|---|---|
| abbreviation | 7 | 0.43 / 0.86 | 0.43 / 0.86 | 0.29 / 0.86 | 0.57 / 1.00 |
| cross_patient | 2 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |
| factoid | 4 | 1.00 / 1.00 | 0.75 / 0.75 | 0.75 / 1.00 | 1.00 / 1.00 |
| followup | 2 | 0.00 / 0.00 | 0.00 / 0.50 | 0.00 / 0.00 | 0.00 / 0.00 |
| injection | 2 | 0.50 / 1.00 | 0.50 / 1.00 | 0.50 / 1.00 | 0.50 / 1.00 |
| multi_chunk | 6 | 0.83 / 1.00 | 0.83 / 1.00 | 0.83 / 1.00 | 0.83 / 1.00 |
| negation | 6 | 0.67 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |
| numeric | 4 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 0.75 / 1.00 |
| table | 5 | 0.60 / 1.00 | 0.80 / 1.00 | 0.60 / 1.00 | 0.80 / 1.00 |
| temporal | 10 | 0.40 / 0.90 | 0.40 / 1.00 | 0.50 / 1.00 | 0.40 / 1.00 |

Cells with n of 2 to 7 are anecdotes, not rates. Two patterns are clear anyway: everything except
follow-ups reaches 100% hit@5 in the default mode, and temporal questions are the weakest at rank 1.

## Cross-patient isolation

Every candidate returned for every question in every mode (208 retrievals) belonged to the asking
patient: **0 cross-patient leaks at the retrieval level**. This holds by construction (one Chroma
collection per patient, no filter to forget) and the run confirms it. The answer-level leak check
(whether a generated answer states another patient's value) is part of the pending answer run.

## Relevance gate

The gate refuses without calling the LLM when the best rerank score is below `MIN_RERANK_SCORE`.
The table replays it at several thresholds on the recorded scores (follow-ups excluded).

| Gate threshold | Unanswerable refused | Answerable wrongly refused |
|---|---|---|
| 1e-05 | 0 / 4 | 0 / 46 |
| 0.0001 | 3 / 4 | 2 / 46 |
| 0.0005 | 4 / 4 | 3 / 46 |
| **0.001 (configured)** | **4 / 4** | **3 / 46** |
| 0.005 | 4 / 4 | 5 / 46 |
| 0.01 | 4 / 4 | 5 / 46 |
| 0.05 | 4 / 4 | 9 / 46 |

At the configured threshold the gate refuses all 4 unanswerable questions without spending an LLM
call, and wrongly refuses 3 of 46 answerable ones (6.5%).

## Failure analysis

I looked at every question where the default mode did not place a correct page first (15 of 48)
and every wrongly refused question. The causes fall into six groups. None is a pipeline bug, so no
code in `backend/app/rag` was changed for this report.

1. **Follow-ups were searched without rewriting (g09, g35; hit@5 0/2).** "And the one before that?"
   has no searchable content, and the evaluation deliberately searches the literal text. In the
   app, `QueryRewriter` turns it into a standalone query first (an LLM step), so these two numbers
   are a lower bound. The answer run, which passes the history, will measure them properly.
2. **"Latest" and "current" questions lose to older reports (g01, g03, g10, g12, g23, g46;
   temporal hit@1 0.40).** The rankers know about wording, not dates, so an older consultation that
   discusses the same drug or test competes with the newest one. In every case the right page is
   still in the top 5 (temporal hit@5 is 1.00), and the prompt tells the model to report each
   value with its report and date when excerpts disagree. The likely effect is a correct but more
   hedged answer, not a wrong one; the answer run will tell. Date-aware boosting would help rank 1
   but is not implemented.
3. **A superseded value outranks the current one (g06).** For "What stage of chronic kidney disease
   does the patient have?" the 2025 consultation (stage G3a) ranks above the 2026 lab report
   (G3b), which only just makes the top 5 (rank 5; BM25 and hybrid miss it). This is the same
   recency blind spot as group 2 with higher stakes, because the stale value is a different answer.
   It is the clearest argument for date-aware ranking or for putting report dates in the prompt.
4. **Wording gap (g40).** "Diabetes in pregnancy" is documented as "gestational diabetes mellitus
   (GDM)". Dense retrieval missed it altogether, and the antenatal booking visit, which discusses
   the same topic, outranks the lab report that states the diagnosis (rank 5 after reranking).
5. **Reranker reorders correct candidates (g16, g25, g49).** MiniLM was trained on short web
   passages and sometimes prefers a neighbouring chunk or another report. This is why
   `hybrid_rerank` has a lower hit@3 than `hybrid` (g01 and g49 slip from rank 3 to 4) even though it
   leads on hit@1 and hit@5. One further miss, g17, is a labelling issue: the ejection fraction
   (58 %) appears on page 1 (narrative) and page 2 (table) of the discharge summary, but the golden
   set lists page 2 only, so the page-1 chunk ranked first counts as a miss although it contains
   the answer. The labels were left as they are rather than adjusted after seeing the results.
   The remaining miss, g51, has the right page second behind a chunk from the same CT report.
6. **The relevance gate wrongly refuses three answerable questions (g14, g31, g43).** In all
   three the correct chunk is ranked first, but the cross-encoder scores it below 0.001 (2.9e-4,
   7.1e-5 and 2.6e-5): short or yes/no questions ("Does the patient have diabetes?", "In which
   position is the baby lying?") look little like a passage to a model trained for web search. The
   raw scores of unanswerable and answerable questions overlap (unanswerable: 2.3e-5 to 2.3e-4;
   those three: 2.6e-5 to 2.9e-4), so no threshold separates them; the sweep above shows the
   trade-off. I did not retune the threshold: with only 4 unanswerable questions, any value chosen
   from this table would be fitted to the evaluation set. A more robust gate would need a second
   signal (for example agreement between dense and BM25 on the top chunk) and a larger labelled set.

**Evaluation environment issue.** Chroma 1.5 on Windows intermittently leaves a freshly bulk-ingested
collection unreadable (`Nothing found on disk`) and does not recover on retry; I saw it in roughly
one run in six while building this report. The harness probes every collection after ingesting and
rebuilds the throw-away store (up to 4 attempts) when that happens, so results are unaffected. The
app itself is not guarded against this.

## Answer-quality results

**To be run by owner with `python -m evals.run --answers --latest`** (about 48 live Gemini calls, rate
limited to 8 per minute, cached on disk; see the harness README). No answer-quality number has
been measured yet, and none is reported here. When the run completes, paste its
`## Answer quality` section into this part. It will contain:

- must_include / must_not_include pass rate (answerable questions)
- unanswerable-handling accuracy
- injection resistance
- citation precision against the golden pages
- answer-level cross-patient leak count (must be 0)
- pass rate per question type

## Limitations

- **Small, synthetic, author-written dataset.** 52 questions over 6 patients and 27 reports, written
  by the same team that built the pipeline. Real reports have messier scans, handwriting and
  layouts, and the questions are probably easier than real clinicians' ones. Treat the numbers as a
  regression baseline, not a performance claim.
- **Small sample.** One question is 2.1 points of hit rate; the 4 to 5 point gaps between modes are
  2 to 3 questions and may not survive a larger set. No confidence intervals were computed.
- **Page-level relevance only.** A hit means the right page, not that the chunk states the answer.
  Several pages hold more than one fact, so a hit can be a near miss, and (see g17) a label can be
  too strict.
- **Retrieval-only for follow-ups.** The rewriter is not exercised until the answer run.
- **Latency is one CPU machine** with models already in memory; it is a relative comparison, not a
  service-level figure.
- **Deterministic answer checks are strict in one direction.** Regexes catch wrong or missing values
  but cannot judge whether a correct answer is well explained, and a refusal is detected by wording.
- **One embedder, one reranker, one chunking setting.** The ablation varies the ranking strategy
  only; chunk size, embedding model and `MIN_RERANK_SCORE` were not swept (apart from the gate
  replay above).
