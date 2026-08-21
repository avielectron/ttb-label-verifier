#!/usr/bin/env bash
# Start script for Render.com free tier.
# Render sets $PORT; default to 8000 for local runs.
set -e

PORT="${PORT:-8000}"

exec uvicorn app.server:app --host 0.0.0.0 --port "$PORT"
