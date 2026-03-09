#!/usr/bin/env bash
# =============================================================
# Copycat — Start backend + frontend together
# Usage: bash start.sh
# Ctrl+C to stop both.
# =============================================================
set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'
info()    { echo -e "${BLUE}[start]${NC} $*"; }
success() { echo -e "${GREEN}[start]${NC} $*"; }

cleanup() {
  info "Shutting down…"
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# ── Backend ──────────────────────────────────────────────────
VENV="backend/.venv/bin/activate"
if [[ ! -f "$VENV" ]]; then
  echo "Virtualenv not found. Run: bash setup.sh"
  exit 1
fi

source "$VENV"
info "Starting backend on http://127.0.0.1:8000 …"
(cd backend && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload) &
BACKEND_PID=$!

# ── Frontend ──────────────────────────────────────────────────
if [[ ! -d "frontend/node_modules" ]]; then
  echo "node_modules not found. Run: bash setup.sh"
  exit 1
fi

info "Starting frontend on http://localhost:3000 …"
(cd frontend && npm run dev) &
FRONTEND_PID=$!

success "Both services started."
echo ""
echo "  Backend:  http://127.0.0.1:8000"
echo "  Docs:     http://127.0.0.1:8000/docs"
echo "  Frontend: http://localhost:3000"
echo ""
echo "  Press Ctrl+C to stop."
echo ""

wait
