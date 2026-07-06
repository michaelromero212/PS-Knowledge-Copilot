#!/usr/bin/env bash
#
# One-command dev startup for PS Knowledge Copilot.
#
# Starts BOTH servers together:
#   - FastAPI backend on :8000 (auto pre-warms the Gemini connection on boot)
#   - Vite frontend on  :5173 (proxies /api -> :8000)
#
# The frontend alone (npm run dev) will show "unknown error" on every query
# because there is no backend to answer it. This script prevents that by always
# bringing both up together. Ctrl+C stops both.
#
# Usage:  ./dev.sh
#
set -euo pipefail
cd "$(dirname "$0")"

PY="./venv/bin/python"
if [ ! -x "$PY" ]; then
  echo "❌ venv not found at ./venv — create it with: python3 -m venv venv && ./venv/bin/pip install -r requirements.txt"
  exit 1
fi

echo "🚀 Starting backend (FastAPI, :8000) — auto-connects to Gemini..."
"$PY" -m uvicorn app.api.main:app --reload --port 8000 &
BACKEND_PID=$!

echo "🎨 Starting frontend (Vite, :5173)..."
( cd frontend && npm run dev ) &
FRONTEND_PID=$!

# Stop both servers on exit / Ctrl+C.
cleanup() {
  echo ""
  echo "👋 Shutting down..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo ""
echo "✅ Both servers starting. Open http://localhost:5173"
echo "   (Backend API docs: http://localhost:8000/api/docs)"
echo "   Press Ctrl+C to stop both."
echo ""

# Wait for either process to exit, then clean up the other.
wait -n "$BACKEND_PID" "$FRONTEND_PID"
