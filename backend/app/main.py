"""Application factory and ASGI entrypoint: ``uvicorn app.main:app --reload``."""

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from app import __version__
from app.api.v1 import router as api_v1
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import BodySizeLimitMiddleware, RequestContextMiddleware
from app.db.session import create_db_engine, create_session_factory, init_db
from app.services.locks import PatientLocks
from app.services.ports import RagPort
from app.services.storage import ReportFileStore
from app.state import AppState

PipelineFactory = Callable[[Settings], RagPort]

# Multipart framing and form fields add a little on top of the PDF itself.
_MULTIPART_OVERHEAD_BYTES = 1024 * 1024

_DESCRIPTION = (
    "Patient-scoped question answering over uploaded medical PDF reports. "
    "Answers are grounded in retrieved passages and carry citations that point "
    "to the exact report page. All errors share one envelope: "
    '`{"error": {"code": "...", "message": "..."}}`.'
)

_TAGS = [
    {"name": "health", "description": "Liveness and active model configuration."},
    {"name": "patients", "description": "Register, list and remove patients."},
    {"name": "reports", "description": "Upload, serve and delete a patient's PDF reports."},
    {"name": "chat", "description": "Ask questions about a patient's records (JSON or SSE)."},
]

logger = structlog.get_logger(__name__)


def build_rag_pipeline(settings: Settings) -> RagPort:
    """Construct the real pipeline; imported here so ML libraries load only when needed."""
    from app.rag.pipeline import RagPipeline

    return RagPipeline(settings.rag_settings())


def create_app(
    settings: Settings | None = None, pipeline_factory: PipelineFactory = build_rag_pipeline
) -> FastAPI:
    """Assemble the application; tests pass their own settings and a fake pipeline."""
    settings = settings or get_settings()
    configure_logging(settings.log_level, settings.log_json)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_db_engine(settings.database_url)
        init_db(engine)
        settings.reports_dir.mkdir(parents=True, exist_ok=True)
        pipeline = pipeline_factory(settings)
        if not settings.skip_warmup:
            await run_in_threadpool(pipeline.warmup)
        app.state.container = AppState(
            settings=settings,
            session_factory=create_session_factory(engine),
            pipeline=pipeline,
            files=ReportFileStore(settings.reports_dir, settings.max_upload_mb),
            locks=PatientLocks(),
        )
        logger.info("startup_complete", version=__version__, llm_configured=settings.llm_configured)
        yield
        engine.dispose()

    app = FastAPI(
        title="Clinical Assistant API",
        description=_DESCRIPTION,
        version=__version__,
        openapi_tags=_TAGS,
        lifespan=lifespan,
    )
    register_exception_handlers(app)

    # Added innermost-first: CORS wraps request logging so even 500s carry CORS headers.
    app.add_middleware(
        BodySizeLimitMiddleware,
        max_body_bytes=settings.max_upload_bytes + _MULTIPART_OVERHEAD_BYTES,
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID", "Content-Disposition"],
    )

    app.include_router(api_v1)
    return app


app = create_app()
