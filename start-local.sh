#!/usr/bin/env bash
# Start the shared backend (port 5050) and the website (port 3000) for local development.
set -e
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$PROJECT_DIR/backend"
if [ ! -x venv/bin/python ]; then
  echo "Creating Python venv (first run, takes a few minutes)..."
  python3 -m venv venv
  venv/bin/pip install -q -r requirements.txt
fi
venv/bin/python -m flask --app server run --port 5050 &
BACKEND_PID=$!
trap 'kill $BACKEND_PID 2>/dev/null' EXIT

cd "$PROJECT_DIR/website"
[ -d node_modules ] || npm install
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:5050 npm run dev
