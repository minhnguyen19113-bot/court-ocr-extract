# Repository Guardrails For Codex

- Do not open, read, OCR, grep, parse, inspect, summarize, or quote any real PDF or derived real-data artifact in `data/raw_pdfs/`, `data/private_pdfs/`, `data/images/`, `data/processed_images/`, `data/ocr_raw/`, `data/ocr_corrected/`, or `outputs/`.
- Work only with code, config, docs, prompts, and synthetic fixtures.
- If sample data is needed, create synthetic data under `data/synthetic/` or `tests/fixtures/`.
- Do not use names, addresses, CCCD/CMND numbers, case details, or wording copied from real people or real PDFs.
- Do not print full OCR text, full names, addresses, CCCD/CMND, or sensitive file names in logs.
- Do not call cloud LLM APIs by default. Cloud LLM adapters must remain opt-in and disabled by config.
- Do not run debug or batch OCR scripts on real user folders unless the user explicitly runs them outside Codex.
