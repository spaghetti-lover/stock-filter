#!/bin/sh
set -e

/app/.venv/bin/yoyo apply --no-config-file \
    --database "$DATABASE_URL" \
    ./db/migrations

exec python3 -B -m uvicorn main:app --host 0.0.0.0 --port 8000
