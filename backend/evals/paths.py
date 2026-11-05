"""Where the evaluation inputs and outputs live on disk."""

from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent

GOLDEN_PATH = BACKEND_DIR / "evals" / "data" / "golden.jsonl"
MANIFEST_PATH = REPO_ROOT / "data" / "synthetic" / "manifest.json"
PDF_ROOT = REPO_ROOT / "data" / "synthetic" / "pdfs"
RESULTS_DIR = BACKEND_DIR / "evals" / "results"
LLM_CACHE_PATH = BACKEND_DIR / ".cache" / "llm_cache.json"
HF_CACHE_DIR = BACKEND_DIR / ".cache" / "huggingface"
