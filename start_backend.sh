#!/usr/bin/env bash
# =============================================================
# Copycat — Start the FastAPI backend (+ optional Celery worker)
# Usage: bash start_backend.sh
# =============================================================
set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'
info() { echo -e "${BLUE}[backend]${NC} $*"; }

VENV="backend/.venv/bin/activate"
if [[ ! -f "$VENV" ]]; then
  echo "Virtualenv not found. Run: bash setup.sh"
  exit 1
fi

source "$VENV"

HOST=${HOST:-127.0.0.1}
PORT=${PORT:-8000}

info "Starting FastAPI on http://${HOST}:${PORT}"
info "API docs: http://${HOST}:${PORT}/docs"

# Celery runs eagerly by default (CELERY_TASK_ALWAYS_EAGER=true).
# Uncomment the lines below to run a real Celery worker backed by Redis.
# info "Starting Celery worker in background …"
# celery -A app.celery_app.celery_app worker --loglevel=info &
# CELERY_PID=$!
# trap "kill $CELERY_PID 2>/dev/null" EXIT

cd backend
uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
