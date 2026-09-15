#!/usr/bin/env bash
# =============================================================
# Copycat — First-time setup
# Run once before starting the application.
# Usage: bash setup.sh
# =============================================================
set -euo pipefail

PYTHON=${PYTHON:-python3.11}
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

info()    { echo -e "${BLUE}[setup]${NC} $*"; }
success() { echo -e "${GREEN}[setup]${NC} $*"; }
error()   { echo -e "${RED}[setup]${NC} $*" >&2; exit 1; }

# ── Check prerequisites ───────────────────────────────────────
command -v "$PYTHON" >/dev/null 2>&1 || error "Python 3.11 not found. Install it from https://python.org"
command -v node     >/dev/null 2>&1 || error "Node.js not found. Install from https://nodejs.org"
command -v npm      >/dev/null 2>&1 || error "npm not found. It ships with Node.js."

info "Python: $($PYTHON --version)"
info "Node:   $(node --version)"

# ── Backend virtualenv ────────────────────────────────────────
info "Creating Python virtualenv in backend/.venv …"
cd backend
$PYTHON -m venv .venv
source .venv/bin/activate

info "Installing core Python requirements …"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt -r requirements-image.txt

info "Video requires FFmpeg and ffprobe on PATH. Audio and OCR are not assessed."

deactivate
cd ..

# ── Frontend dependencies ─────────────────────────────────────
info "Installing frontend npm packages …"
cd frontend
npm ci --silent
cd ..

# ── Create data directories ───────────────────────────────────
mkdir -p backend/data/uploads backend/data/reports

success "Setup complete!"
echo ""
echo "  Start the backend:   bash start_backend.sh"
echo "  Start the frontend:  bash start_frontend.sh"
echo "  Start both:          bash start.sh"
echo ""
