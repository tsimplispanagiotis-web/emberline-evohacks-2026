#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PYTHON=${PYTHON:-python3}
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo 'Python 3.10+ required. Install Python and try again.' >&2
  exit 1
fi
if [ ! -d .venv ]; then "$PYTHON" -m venv .venv; fi
. .venv/bin/activate
python -m pip install -r requirements.txt
printf '\nEMBERLINE 3.0 — local, synthetic-only sandbox\nOpen: http://127.0.0.1:8000\nTo stop: Ctrl+C\n\n'
exec python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
