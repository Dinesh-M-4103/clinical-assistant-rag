from fastapi import APIRouter

from app import __version__
from app.api.deps import SettingsDep
from app.schemas.health import Health

router = APIRouter(tags=["health"])


@router.get("/health", summary="Service status and active model configuration")
def health(settings: SettingsDep) -> Health:
    return Health(
        status="ok",
        llm_configured=settings.llm_configured,
        embedding_model=settings.embedding_model,
        reranker_model=settings.reranker_model,
        version=__version__,
    )
