#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-gpu.txt
pip install -e .

mkdir -p data/raw_pdfs/uploads outputs/excel outputs/json outputs/logs

if [ ! -f .env ]; then
  cp .env.example .env
fi

echo "Ezycloudx setup done. Default CLI path does not require Ollama."
