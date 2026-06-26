#!/usr/bin/env bash
set -euo pipefail

source .venv/bin/activate

INPUT_DIR="${1:-data/raw_pdfs/uploads}"
OUTPUT_FILE="${2:-outputs/excel/result.xlsx}"

python -m scripts.run_batch \
  --input-dir "$INPUT_DIR" \
  --output "$OUTPUT_FILE" \
  --processing-mode local-only \
  --max-pages-before-marker "${MAX_PAGES_BEFORE_CONTENT_MARKER:-5}" \
  --remove-red-stamp \
  --no-local-llm \
  --force
