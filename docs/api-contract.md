# Clinical Assistant — Shared Contract

Single source of truth for the backend, RAG package, synthetic data/evals and frontend.
Everything runs locally. No deployment, no auth (documented scope limit).

- Backend: `http://localhost:8000`, all routes under `/api/v1`. FastAPI auto-docs at `/docs`.
- Frontend: `http://localhost:5173` (Vite). CORS allow-list comes from `CORS_ORIGINS` (never `*`).
- Python 3.12 via `uv` (venv at `backend/.venv`). Node 24 / npm. Everything installs INSIDE this repo folder.
- All model/data caches live inside the repo (gitignored): `HF_HOME=backend/.cache/huggingface`,
  `UV_CACHE_DIR=backend/.cache/uv`, uploaded PDFs + SQLite + Chroma in `backend/storage/`.
- Never commit secrets; `backend/.env` exists (gitignored) with `GEMINI_API_KEY`, `GEMINI_MODEL`, `CORS_ORIGINS`.
  The default is `GEMINI_BACKEND=studio` (Gemini Developer API via `genai.Client(api_key=...)`) with model
  `gemini-3.5-flash-lite`. `vertex` is an opt-in setting; by default the key shape is not used to pick Vertex.

## Domain

- **Patient** — keyed by `uhid` (string, 3–32 chars, `[A-Za-z0-9_-]`).
- **Report** — one PDF belonging to one patient. Ingested into that patient's own vector collection.
- **Citation** — a retrieved chunk. IDs `C1..Cn` are scoped to ONE chat response.

## REST

Errors always: `{"error": {"code": "<snake_case>", "message": "<human text>"}}` with a proper HTTP status
(400 validation/bad file, 404 not_found, 409 conflict, 413 file_too_large, 415 unsupported_media_type,
422 request validation (same envelope), 502 llm_unavailable, 500 internal_error).

| Method | Path | Body | Success |
|---|---|---|---|
| GET | `/api/v1/health` | – | `Health` |
| GET | `/api/v1/patients` | – | `Patient[]` (newest first) |
| POST | `/api/v1/patients` | `PatientCreate` | 201 `Patient` (409 `patient_exists`) |
| GET | `/api/v1/patients/{uhid}` | – | `Patient` |
| DELETE | `/api/v1/patients/{uhid}` | – | 204 (removes reports, files, vectors) |
| GET | `/api/v1/patients/{uhid}/reports` | – | `Report[]` (newest first) |
| POST | `/api/v1/patients/{uhid}/reports` | multipart: `file` (PDF), `name`, `category`, `notes?` | 201 `Report` |
| DELETE | `/api/v1/patients/{uhid}/reports/{report_id}` | – | 204 (file + vectors + row) |
| GET | `/api/v1/patients/{uhid}/reports/{report_id}/file` | – | `application/pdf`, inline |
| POST | `/api/v1/patients/{uhid}/chat` | `ChatRequest` | `ChatResponse` |
| POST | `/api/v1/patients/{uhid}/chat/stream` | `ChatRequest` | SSE (below) |

Upload rules: only real PDFs (magic bytes `%PDF-`, not just extension), max `MAX_UPLOAD_MB` (default 25),
filename sanitised, stored under server-generated ids (never user-supplied paths), `category` ∈
`lab | imaging | discharge | prescription | consultation | other`. A PDF with no extractable text → 400
`no_extractable_text`.

### Schemas (JSON)

```jsonc
// PatientCreate
{ "uhid": "MG25001", "name": "Asha Verma", "age": 54, "gender": "female", "summary": "optional text" }
// gender ∈ "male" | "female" | "other"; age 0..130

// Patient
{ "uhid": "MG25001", "name": "...", "age": 54, "gender": "female", "summary": "..." | null,
  "report_count": 3, "created_at": "2026-11-04T10:00:00Z" }

// Report
{ "report_id": "uuid", "uhid": "MG25001", "name": "CBC Report", "category": "lab", "notes": "..." | null,
  "original_filename": "cbc.pdf", "page_count": 4, "chunk_count": 17, "size_bytes": 123456,
  "uploaded_at": "2026-11-04T10:00:00Z", "file_url": "/api/v1/patients/MG25001/reports/<id>/file" }

// ChatRequest — history = previous turns (oldest first), max 10 used server-side
{ "question": "What is the latest HbA1c?",
  "history": [ { "role": "user" | "assistant", "content": "..." } ] }

// Citation
{ "id": "C1", "report_id": "uuid", "report_name": "CBC Report", "category": "lab",
  "page": 2, "section": "Laboratory Results" | null, "text": "chunk text", "score": 0.83, "cited": true }
// "cited" = the model actually referenced [C1] in its answer. All retrieved chunks are returned
// (cited ones flagged) so the UI can show "what the model saw" vs "what it used".

// ChatResponse
{ "answer": "HbA1c was 7.8% on ... [C1].", "citations": [Citation], "trace": Trace }

// Trace — powers the "How this answer was made" drawer
{ "intent": "question" | "greeting" | "off_topic",
  "rewritten_query": "standalone query" | null,
  "insufficient_evidence": false,
  "candidates": [ { "id": "C1", "dense_rank": 1 | null, "bm25_rank": 3 | null,
                    "fused_score": 0.031, "rerank_score": 0.91 | null } ],
  "timings_ms": { "rewrite": 210, "retrieval": 35, "rerank": 120, "generation": 1400, "total": 1800 },
  "models": { "llm": "gemini-2.5-flash", "embedding": "BAAI/bge-small-en-v1.5",
              "reranker": "cross-encoder/ms-marco-MiniLM-L-6-v2" },
  "tokens": { "prompt": 1200, "completion": 180 } | null }

// Health
{ "status": "ok", "llm_configured": true, "embedding_model": "...", "reranker_model": "...", "version": "0.1.0" }
```

### SSE — `POST /api/v1/patients/{uhid}/chat/stream`

`Content-Type: text/event-stream`. Events (each `event: <name>` + `data: <json>`):

1. `meta` — `{"intent": "...", "rewritten_query": "..."|null}` (optional, sent once retrieval is done)
2. `citations` — `Citation[]` (all retrieved chunks, `cited:false` initially; sent before tokens)
3. `token` — `{"text": "partial text"}` (many)
4. `done` — full `ChatResponse` (authoritative: final answer, citations with `cited` flags set, trace)
5. `error` — `{"code": "...", "message": "..."}` (terminal; stream closes)

The frontend renders `token` text live and replaces everything with `done` when it arrives.
Greetings/off-topic/insufficient-evidence answers are produced without calling the LLM generator
(still emit `token` + `done`, `citations` empty).

## RAG package interface (`backend/app/rag/`)

`app/rag` MUST NOT import FastAPI/SQLAlchemy. API layer talks to it only through `RagPipeline`
(`app/rag/pipeline.py`) plus the dataclasses in `app/rag/types.py`:

```python
@dataclass(frozen=True)
class IngestResult:  page_count: int; chunk_count: int

class RagPipeline:
    def __init__(self, settings: RagSettings): ...          # builds embedder, store, reranker, llm lazily
    def ingest_pdf(self, *, patient_id: str, report_id: str, report_name: str,
                   category: str, pdf_path: Path) -> IngestResult   # raises NoExtractableTextError
    def delete_report(self, *, patient_id: str, report_id: str) -> None
    def delete_patient(self, *, patient_id: str) -> None
    def answer(self, *, patient_id: str, question: str, history: Sequence[Turn]) -> RagAnswer
    def answer_stream(self, *, patient_id: str, question: str, history: Sequence[Turn]) -> Iterator[RagEvent]
    # RagEvent = MetaEvent | CitationsEvent | TokenEvent | DoneEvent | ErrorEvent  (dataclasses in types.py)
    def warmup(self) -> None                                  # load models (called in app lifespan)
```

`RagAnswer`/`DoneEvent` carry `answer: str`, `citations: list[CitationDTO]`, `trace: TraceDTO` whose fields
mirror the JSON above 1:1 (the API layer maps them to Pydantic response models).
`RagSettings` is a plain frozen dataclass built from app Settings (no pydantic-settings import inside rag).
Embedding model/reranker/LLM are behind small Protocols (`Embedder`, `Reranker`, `LLMClient`) so tests inject fakes.

## Defaults (all configurable via env / Settings)

- Embeddings: `BAAI/bge-small-en-v1.5` (local, normalised, query prefix per BGE docs)
- Reranker: `cross-encoder/ms-marco-MiniLM-L-6-v2` (local)
- Chunk target ≈ 300 tokens, overlap ≈ 50, sentence/section aware; dense top 20 + BM25 top 20 → RRF (k=60) → rerank → top 5
- Relevance gate: if best rerank score is below `MIN_RERANK_SCORE` → `insufficient_evidence=true` answer without LLM call
- Vector store: ChromaDB `PersistentClient(backend/storage/chroma)`, ONE collection per patient (`patient_<uhid>`),
  collection metadata stores embedding model name; mismatch → explicit error, never silent delete
- DB: SQLite `backend/storage/app.db`, SQLAlchemy 2.0 typed models, tables `patients`, `reports`
