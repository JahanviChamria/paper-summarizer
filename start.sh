#!/usr/bin/env bash
# Starts the FastAPI backend (port 8000) and Vite frontend (port 5173) together.
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "ERROR: ANTHROPIC_API_KEY is not set. Export it and re-run." >&2
  exit 1
fi

cleanup() {
  echo ""
  echo "Shutting down…"
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# --- Backend ---
echo "Starting backend…"
cd "$ROOT/backend"
if [ ! -d ".venv" ]; then
  python -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate
pip install -q -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# --- Frontend ---
echo "Starting frontend…"
cd "$ROOT/frontend"
if [ ! -d "node_modules" ]; then
  npm install
fi
npm run dev -- --host &
FRONTEND_PID=$!

# --- Wait for both to be reachable ---
wait_for() {
  local url="$1" name="$2" tries=0
  until curl -s -o /dev/null "$url"; do
    tries=$((tries + 1))
    if [ "$tries" -gt 60 ]; then
      echo "Timed out waiting for $name." >&2
      exit 1
    fi
    sleep 1
  done
}

wait_for "http://localhost:8000/health" "backend"
wait_for "http://localhost:5173" "frontend"

echo ""
echo "Ready at http://localhost:5173"

wait
