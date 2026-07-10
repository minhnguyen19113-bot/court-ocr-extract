# Testing

Last updated: 2026-07-09

## Allowed In Codex

- Unit tests.
- Contract tests.
- Schema/control-flow tests using minimal non-real fixtures under `tests/fixtures/`.
- `python -m compileall src scripts -q`.
- Synthetic smoke only when it creates explicitly synthetic artifacts.
- Repo guardrail scripts that do not inspect real data folders.
- Architecture audit scripts that inspect only code/config/docs/prompts/scripts/tests.

## Not Allowed In Codex

- Real PDF OCR.
- Real OCR text parsing.
- Real Excel output inspection.
- Real debug output inspection.
- Full/pilot workflow on real user folders.
- Cloud OCR/extraction calls.

## Test Categories

| Category | Command/example | Purpose |
| --- | --- | --- |
| Syntax/import smoke | `python -m compileall src scripts -q` | Catch syntax/import-bytecode issues. |
| Repo safety guardrails | `python -m scripts.check_repo_guardrails` | Detect protected paths, cloud defaults, Tesseract default-like references. |
| Architecture guardrails | `python -m scripts.check_architecture_guardrails` | Detect architecture default regressions and known cleanup warnings. |
| Inventory/import graph | `python -m scripts.repo_inventory`, `python -m scripts.import_graph` | Produce review artifacts, not deletion proof. |
| Backend availability | `python -m scripts.check_ocr_backend --backend surya` | Check runtime adapter availability without running real PDFs. |
| Unit/contract tests | `python -m pytest -p no:cacheprovider` | Verify synthetic control-flow contracts. |
| Optional lint | `python -m ruff check src scripts tests` | Run only when `ruff` is installed in `.venv`; do not fake pass if missing. |

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

After Phase 1D, `scripts.check_architecture_guardrails` should also fail if README/docs/scripts reintroduce executable run instructions for the removed `app_fastapi` or `app_streamlit` apps.

## Phase 1C Verification Commands

```powershell
.\.venv\Scripts\python -B -m compileall src scripts -q
.\.venv\Scripts\python -B -m scripts.project_snapshot
.\.venv\Scripts\python -B -m scripts.check_repo_guardrails
.\.venv\Scripts\python -B -m scripts.check_architecture_guardrails
.\.venv\Scripts\python -B -m scripts.repo_inventory
.\.venv\Scripts\python -B -m scripts.import_graph
.\.venv\Scripts\python -B -m scripts.check_ocr_backend --backend surya
.\.venv\Scripts\python -B -m pytest -p no:cacheprovider
git diff --check
git status --short
```

## Test Interpretation

Synthetic passing tests mean the repo contracts still execute. They do not mean the OCR/extraction quality is acceptable on real court PDFs.
