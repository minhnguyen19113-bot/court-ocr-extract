# Security And Privacy

Last updated: 2026-07-07

## Protected Data

Do not commit or inspect real:

- PDFs
- rendered page images
- processed images
- OCR raw/corrected text
- extraction JSON
- Excel outputs
- debug UI generated from real data
- logs containing names, addresses, IDs, case details, or sensitive filenames

## Codex Boundary

Codex may inspect:

- code
- config
- docs
- prompts
- minimal synthetic fixtures

Codex must not inspect:

- `data/raw_pdfs/`
- `data/private_pdfs/`
- `data/images/`
- `data/processed_images/`
- `data/ocr_raw/`
- `data/ocr_corrected/`
- `outputs/` except explicit synthetic smoke paths approved in `AGENTS.md`

## Cloud Boundary

- Cloud OCR/extraction is disabled by default.
- Cloud adapters may exist for opt-in benchmarks only.
- No cloud LLM API calls are allowed unless Project Owner explicitly requests them.

## Logging

Terminal logs must show metrics and paths only when safe. They must not print full OCR text, full names, addresses, CCCD/CMND, or sensitive filenames.

## Git Hygiene

`.gitignore` should continue excluding real data and derived artifacts. `scripts.check_repo_guardrails` should be run before staging or commit.
