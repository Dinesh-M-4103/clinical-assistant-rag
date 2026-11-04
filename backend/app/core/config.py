"""Application settings, loaded from the environment and ``backend/.env``."""

from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

if TYPE_CHECKING:
    from app.rag.config import RagSettings

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Every tunable of the backend; relative paths are anchored at ``backend/``."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    log_level: str = "INFO"
    log_json: bool = False

    storage_dir: Path = BACKEND_DIR / "storage"
    hf_cache_dir: Path = BACKEND_DIR / ".cache" / "huggingface"
    max_upload_mb: int = Field(default=25, ge=1, le=500)
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    skip_warmup: bool = False

    embedding_model: str = "BAAI/bge-small-en-v1.5"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    gemini_model: str = "gemini-3.5-flash-lite"
    gemini_api_key: SecretStr | None = None
    gemini_backend: Literal["studio", "vertex"] = "studio"
    gemini_max_rpm: int = Field(default=8, ge=1)
    min_rerank_score: float | None = None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: Any) -> Any:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("cors_origins")
    @classmethod
    def _reject_wildcard(cls, origins: list[str]) -> list[str]:
        if "*" in origins:
            raise ValueError("CORS_ORIGINS must list explicit origins, never '*'")
        return origins

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def database_url(self) -> str:
        return f"sqlite:///{(self.storage_dir / 'app.db').as_posix()}"

    @property
    def chroma_dir(self) -> Path:
        return self.storage_dir / "chroma"

    @property
    def reports_dir(self) -> Path:
        return self.storage_dir / "reports"

    @property
    def api_key(self) -> str | None:
        """The Gemini key as plain text, or ``None`` when unset or blank."""
        if self.gemini_api_key is None:
            return None
        return self.gemini_api_key.get_secret_value().strip() or None

    @property
    def llm_configured(self) -> bool:
        return self.api_key is not None

    def rag_settings(self) -> "RagSettings":
        """Translate app settings into the RAG package's plain dataclass.

        Imported lazily so the API layer never loads ML dependencies just to
        read configuration.
        """
        from app.rag.config import RagSettings

        overrides: dict[str, Any] = {}
        if self.min_rerank_score is not None:
            overrides["min_rerank_score"] = self.min_rerank_score
        return RagSettings(
            chroma_dir=self.chroma_dir,
            hf_cache_dir=self.hf_cache_dir,
            embedding_model=self.embedding_model,
            reranker_model=self.reranker_model,
            llm_model=self.gemini_model,
            gemini_api_key=self.api_key,
            gemini_backend=self.gemini_backend,
            gemini_max_rpm=self.gemini_max_rpm,
            **overrides,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
