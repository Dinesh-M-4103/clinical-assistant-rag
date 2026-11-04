# Clinical Assistant: backend

FastAPI service that stores patients and their PDF reports and answers questions about them through the RAG pipeline in `app/rag`. The HTTP contract lives in [`../docs/api-contract.md`](../docs/api-contract.md); interactive docs are served at `/docs` while the app runs.

## Layout

```
app/
  main.py        create_app() factory, lifespan (db, pipeline warm-up), middleware, CORS
  core/          settings, structured logging, request middleware, error envelope
  db/            SQLAlchemy 2.0 models (patients, reports), engine and session factory
  schemas/       Pydantic request/response models that mirror the contract
  services/      business logic: patients, reports (file storage + ingestion), chat/SSE mapping
  api/           thin /api/v1 routers and the dependency wiring
  rag/           retrieval pipeline (separate package, no web imports)
tests/           API and service tests run against a FakePipeline
```

Request flow: router (validation, HTTP status) -> service (transactions, file handling, locks) -> `RagPort` protocol (`services/ports.py`). The API never imports the concrete pipeline except inside the lifespan factory, so it starts and is testable without loading ML models.

## Run

From this folder, using the project virtualenv (`.venv`) and keeping every cache inside the repo:

```powershell
$env:HF_HOME = "$PWD\.cache\huggingface"
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Settings come from the environment and `backend/.env` (copy `.env.example`):

| Variable | Default | Meaning |
|---|---|---|
| `GEMINI_API_KEY` | none | LLM key; without it the API runs but answers fail with 502 |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | generation model |
| `GEMINI_BACKEND` | `studio` | `studio` (Gemini Developer API, also for `AQ.` keys) or `vertex` |
| `GEMINI_MAX_RPM` | `8` | client-side cap on LLM requests per minute (free tier allows about 10) |
| `CORS_ORIGINS` | `http://localhost:5173` | comma-separated allow-list; `*` is rejected |
| `MAX_UPLOAD_MB` | `25` | hard cap on one PDF |
| `STORAGE_DIR` | `backend/storage` | SQLite file, Chroma data and uploaded PDFs |
| `EMBEDDING_MODEL`, `RERANKER_MODEL` | contract defaults | local Hugging Face models |
| `MIN_RERANK_SCORE` | RAG default | relevance gate override |
| `SKIP_WARMUP` | `false` | skip loading models at startup |
| `LOG_JSON`, `LOG_LEVEL` | `false`, `INFO` | structured log format and level |

Models are loaded at startup, so the first launch downloads them into `HF_HOME` and takes a while.

## Data and migrations

Storage is `storage/app.db` (SQLite, WAL, foreign keys on), `storage/chroma/` (vectors) and `storage/reports/<uhid>/<report_id>.pdf`. Tables are created on startup with `create_all`; there is deliberately no Alembic because the schema is two small tables. Changing a model means deleting `storage/` (local development data) or altering the table by hand.

## Behaviour worth knowing

- Uploads are validated by magic bytes, streamed to disk under a hard size cap and removed (file, vectors and row) if ingestion fails.
- Ingestion and deletion take a per-patient lock, so one patient's vector collection never has two writers; different patients run in parallel.
- Reports are only served through a database lookup by `report_id` within the patient in the URL; no client-supplied path ever reaches the filesystem.
- Every error, including validation failures and unexpected crashes, uses `{"error": {"code", "message"}}` and never includes stack traces or paths. Each response carries `X-Request-ID`, which also appears in the access log.
- The chat stream runs the synchronous pipeline generator in a worker thread; a client disconnect closes it.

## Test and lint

```powershell
.venv\Scripts\python.exe -m pytest tests/api tests/services
.venv\Scripts\python.exe -m ruff check app tests
.venv\Scripts\python.exe -m ruff format --check app tests
.venv\Scripts\python.exe -m mypy app tests/api tests/services tests/conftest.py tests/fakes.py tests/helpers.py
```
