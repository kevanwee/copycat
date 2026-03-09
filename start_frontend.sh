#!/usr/bin/env bash
# =============================================================
# Copycat — Start the Next.js frontend (development server)
# Usage: bash start_frontend.sh
# =============================================================
set -euo pipefail

BLUE='\033[0;34m'
NC='\033[0m'
info() { echo -e "${BLUE}[frontend]${NC} $*"; }

if [[ ! -d "frontend/node_modules" ]]; then
  echo "node_modules not found. Run: bash setup.sh"
  exit 1
fi

PORT=${FRONTEND_PORT:-3000}
info "Starting Next.js dev server on http://localhost:${PORT}"

cd frontend
PORT=$PORT npm run dev
