#!/usr/bin/env bash
# Developer tasks for macOS, Linux and Git Bash. Windows PowerShell users: scripts/dev.ps1.
#
#   ./scripts/dev.sh <setup|backend|frontend|dev|seed|test|lint|clean|eval|help>
#
# Every cache (Hugging Face models, uv, Playwright browsers) is kept inside the repo.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

export HF_HOME="$BACKEND/.cache/huggingface"
export UV_CACHE_DIR="$BACKEND/.cache/uv"
export PLAYWRIGHT_BROWSERS_PATH="$FRONTEND/.playwright"

if [ -x "$BACKEND/.venv/Scripts/python.exe" ]; then
  PY="$BACKEND/.venv/Scripts/python.exe"
else
  PY="$BACKEND/.venv/bin/python"
fi

require_venv() {
  [ -x "$PY" ] || { echo "Backend environment missing. Run: ./scripts/dev.sh setup" >&2; exit 1; }
}

setup() {
  (cd "$BACKEND" && uv sync)
  (cd "$FRONTEND" && npm install)
  if [ ! -f "$BACKEND/.env" ]; then
    cp "$BACKEND/.env.example" "$BACKEND/.env"
    echo "Created backend/.env - add your GEMINI_API_KEY to it."
  fi
}

backend() {
  require_venv
  cd "$BACKEND"
  "$PY" -m uvicorn app.main:app --reload --reload-dir app --host 127.0.0.1 --port 8000
}

frontend() {
  cd "$FRONTEND"
  npm run dev
}

dev() {
  # Ctrl+C or exit of the web app takes the whole process group, and so the API, down with it.
  trap 'trap - INT TERM EXIT; kill 0' INT TERM EXIT
  backend &
  frontend
}

seed() {
  require_venv
  "$PY" "$BACKEND/scripts/seed_demo.py"
}

test_all() {
  require_venv
  (cd "$BACKEND" && "$PY" -m pytest)
  (cd "$FRONTEND" && npm test)
}

lint() {
  require_venv
  (
    cd "$BACKEND"
    "$PY" -m ruff check .
    "$PY" -m ruff format --check .
    "$PY" -m mypy app tests scripts evals
  )
  (cd "$FRONTEND" && npm run lint && npm run typecheck)
}

run_eval() {
  # Extra arguments go to the CLI, e.g. ./scripts/dev.sh eval --answers
  require_venv
  (cd "$BACKEND" && "$PY" -m evals.run "$@")
}

clean() {
  rm -rf "$BACKEND/.pytest_cache" "$BACKEND/.mypy_cache" "$BACKEND/.ruff_cache"
  rm -rf "$FRONTEND/dist" "$FRONTEND/coverage" "$FRONTEND/test-results"
  find "$BACKEND" \( -name .venv -o -name .cache \) -prune -o -name __pycache__ -type d -exec rm -rf {} +
}

usage() {
  cat <<'USAGE'
Usage: ./scripts/dev.sh <task>

  setup     install backend (uv) and frontend (npm) dependencies, create backend/.env
  backend   run the API on http://localhost:8000 with auto-reload
  frontend  run the web app on http://localhost:5173
  dev       run backend and frontend together (Ctrl+C stops both)
  seed      load the synthetic demo patients into the running backend
  test      backend pytest (fast set) and frontend Vitest
  lint      ruff, mypy, ESLint and tsc
  eval      retrieval ablation over the golden questions (no LLM calls); --answers adds answer quality
  clean     remove build output and tool caches (keeps models, venv, node_modules, storage)
USAGE
}

case "${1:-help}" in
  setup) setup ;;
  backend) backend ;;
  frontend) frontend ;;
  dev) dev ;;
  seed) seed ;;
  test) test_all ;;
  lint) lint ;;
  clean) clean ;;
  eval) shift; run_eval "$@" ;;
  help | -h | --help) usage ;;
  *) usage >&2; exit 2 ;;
esac
