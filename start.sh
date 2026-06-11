#!/usr/bin/env bash
# start.sh — Launch PostureMonitor (one-shot script for macOS / Linux)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# ── 1. Build frontend if static dir is missing or stale ──────────────────────
STATIC_DIR="$BACKEND_DIR/static"
if [ ! -f "$STATIC_DIR/index.html" ]; then
  echo "🔨  Building SvelteKit frontend…"
  cd "$FRONTEND_DIR"
  yarn install --frozen-lockfile
  yarn build
  cd "$SCRIPT_DIR"
fi

# ── 2. Install Python deps (into venv if present) ────────────────────────────
cd "$BACKEND_DIR"
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi

if ! python -c "import fastapi" 2>/dev/null; then
  echo "🐍  Installing Python dependencies…"
  pip install -r requirements.txt
fi

# ── 3. Launch ─────────────────────────────────────────────────────────────────
echo "🚀  Starting PostureMonitor at http://127.0.0.1:8000"
python main.py
