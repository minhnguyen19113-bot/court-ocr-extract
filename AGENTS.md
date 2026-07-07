# Repository Guardrails For Codex

- Do not open, read, OCR, grep, parse, inspect, summarize, or quote any real PDF or derived real-data artifact in `data/raw_pdfs/`, `data/private_pdfs/`, `data/images/`, `data/processed_images/`, `data/ocr_raw/`, `data/ocr_corrected/`, or `outputs/`.
- Exception: Codex may create and inspect artifacts under explicit synthetic smoke paths such as `outputs/debug_visual/synthetic_smoke/`, `outputs/extraction_draft/synthetic_smoke/`, `outputs/excel/synthetic_smoke.xlsx`, and `outputs/qa/synthetic_smoke_report.json`, because these are generated from non-real contract fixtures by `python -m scripts.smoke_synthetic_debug`.
- Work only with code, config, docs, prompts, and minimal contract fixtures.
- Do not use fake/sample fixtures to judge OCR or extraction quality. Real quality validation must be run by the user on real court PDFs outside Codex.
- If automated tests need input, use minimal non-real contract fixtures under `tests/fixtures/`; these fixtures are only for schema/control-flow tests.
- Do not use names, addresses, CCCD/CMND numbers, case details, or wording copied from real people or real PDFs.
- Do not print full OCR text, full names, addresses, CCCD/CMND, or sensitive file names in logs.
- Do not call cloud LLM APIs by default. Cloud LLM adapters must remain opt-in and disabled by config.
- Do not run debug or batch OCR scripts on real user folders inside Codex. The user may run the real-data pilot/full workflow directly outside Codex.
