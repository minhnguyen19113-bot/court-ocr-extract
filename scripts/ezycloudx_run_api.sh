#!/usr/bin/env bash
set -euo pipefail

source .venv/bin/activate

export ENABLE_CLOUD_LLM_EXTRACTION="${ENABLE_CLOUD_LLM_EXTRACTION:-false}"
export ENABLE_LOCAL_LLM_EXTRACTION="${ENABLE_LOCAL_LLM_EXTRACTION:-true}"
export ENABLE_MOCK_OCR="${ENABLE_MOCK_OCR:-false}"
export ENABLE_MOCK_LOCAL_LLM="${ENABLE_MOCK_LOCAL_LLM:-false}"
export LOCAL_LLM_PROVIDER="${LOCAL_LLM_PROVIDER:-ollama}"
export LOCAL_LLM_BASE_URL="${LOCAL_LLM_BASE_URL:-http://127.0.0.1:11434}"

uvicorn app_fastapi.main:app --host 0.0.0.0 --port "${APP_PORT:-8000}"
