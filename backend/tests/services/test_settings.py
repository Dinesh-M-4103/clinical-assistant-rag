from pathlib import Path

import pytest

from app.core.config import Settings
from app.rag.config import DEFAULT_MIN_RERANK_SCORE


def test_paths_derive_from_storage_dir(tmp_path: Path) -> None:
    settings = Settings(_env_file=None, storage_dir=tmp_path)

    assert settings.database_url == f"sqlite:///{(tmp_path / 'app.db').as_posix()}"
    assert settings.chroma_dir == tmp_path / "chroma"
    assert settings.reports_dir == tmp_path / "reports"
    assert settings.max_upload_bytes == 25 * 1024 * 1024


def test_rag_settings_translate_app_settings(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        storage_dir=tmp_path,
        gemini_api_key="  AQ.dummy  ",
        gemini_model="gemini-test",
        gemini_backend="vertex",
        min_rerank_score=0.3,
    )

    rag = settings.rag_settings()

    assert rag.chroma_dir == tmp_path / "chroma"
    assert rag.llm_model == "gemini-test"
    assert rag.gemini_backend == "vertex"
    assert rag.gemini_api_key == "AQ.dummy"
    assert rag.min_rerank_score == 0.3


def test_rag_defaults_apply_when_nothing_is_overridden(tmp_path: Path) -> None:
    rag = Settings(_env_file=None, storage_dir=tmp_path).rag_settings()

    assert rag.gemini_backend == "studio"
    assert rag.llm_model == "gemini-3.5-flash-lite"
    assert rag.gemini_max_rpm == 8
    assert rag.gemini_api_key is None
    assert rag.min_rerank_score == DEFAULT_MIN_RERANK_SCORE


@pytest.mark.parametrize("blank", ["", "   "])
def test_blank_api_key_counts_as_unconfigured(blank: str) -> None:
    assert not Settings(_env_file=None, gemini_api_key=blank).llm_configured


def test_secret_key_is_not_exposed_by_repr() -> None:
    assert "AQ.dummy" not in repr(Settings(_env_file=None, gemini_api_key="AQ.dummy"))
