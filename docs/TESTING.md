# Testing

Last updated: 2026-07-07

## Allowed In Codex

- Unit tests.
- Contract tests.
- Schema/control-flow tests using minimal non-real fixtures under `tests/fixtures/`.
- `python -m compileall src scripts -q`.
- Synthetic smoke only when it creates explicitly synthetic artifacts.
- Repo guardrail scripts that do not inspect real data folders.

## Not Allowed In Codex

- Real PDF OCR.
- Real OCR text parsing.
- Real Excel output inspection.
- Real debug output inspection.
- Full/pilot workflow on real user folders.
- Cloud OCR/extraction calls.

## Phase 1B Verification Commands

```powershell
git status --short
python -m compileall src scripts -q
python -m pytest -p no:cacheprovider
python -m scripts.project_snapshot
python -m scripts.check_repo_guardrails
git diff --check
```

After Phase 1B, `scripts.check_repo_guardrails` should pass unless a new real-data path, cloud default, or main/default Tesseract reference was introduced.

## Test Interpretation

Synthetic passing tests mean the repo contracts still execute. They do not mean the OCR/extraction quality is acceptable on real court PDFs.
