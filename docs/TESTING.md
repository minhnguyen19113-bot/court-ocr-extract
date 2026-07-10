# Testing

Last updated: 2026-07-10

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

After Phase 1E, `scripts.check_architecture_guardrails` phải fail nếu canonical `src/court_ocr_extract/excel_writer.py` bị thiếu hoặc import `court_ocr_extract.excel`/`court_ocr_extract.export.excel_writer` quay lại. Path compatibility cũ còn tồn tại sẽ tạo warning.

`tests/test_excel_writer_contract.py` chỉ tạo workbook synthetic trong `tmp_path`, mở lại bằng `openpyxl`, và kiểm sheet/header hiện tại. Test này không đọc hoặc ghi Excel real-data trong `outputs/`.

After Phase 1F, `scripts.check_architecture_guardrails` phải fail nếu canonical extraction paths thiếu, legacy extraction import quay lại, hoặc tests chứa direct network call. `scripts.check_extractor` mặc định chỉ kiểm static configuration và không gọi model endpoint.

`tests/test_extraction_consolidation.py` dùng fake Local LLM response và synthetic `OCRCacheRecord`; test kiểm `case_id`, fields, evidence, warnings và review helper mà không ghi `outputs/`.

TOOLKIT-1 tests chỉ dùng hai JSONL fixtures đã redact trong `tests/fixtures/` và `tmp_path`. Tests cover manifest validation, PII detection/redaction, perfect/mismatch metrics, participant missing/extra, evidence/source coverage, safe report và CLI. Không test nào đọc `data/`, `data_private/` hoặc `outputs/`.

Preprocess safety tests dùng ảnh RGB synthetic trong `tmp_path` để kiểm red HSV mask/removal, bảo toàn chữ đen, no-seal behavior, color-before-grayscale order, safe deskew, blank fallback và debug HTML. Chúng không mở PDF, không gọi OCR/Surya và không chứng minh ngưỡng phù hợp cho scan thật.

Preprocess v2 tests mở rộng sang HSV/Lab/RGB metadata, `neutralize|inpaint|white_fill`, black-text overlap protection, red residual, text `light`, strong-mode guard, blank/no-seal và mọi debug artifact. Passing tests chỉ chứng minh contract synthetic, không chứng minh chất lượng scan thật.

Preprocessed OCR wiring tests monkeypatch render/preprocess và fake `_run_surya_on_images`/backend. Tests kiểm final path, Mode 3 metadata, cache/manifest/artifacts, rendered-original branch và exception safe copy mà không mở PDF hoặc gọi Surya thật.

Surya version-guard tests monkeypatch distribution version và import/runtime entrypoints. Chúng kiểm 0.20.0 pass, 0.21.1/missing fail trước import, reinstall message và `check_ocr_backend` không gọi `ocr_pdf_prefix`.

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

## Phase 1E Verification Commands

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

## Phase 1F Verification Commands

```powershell
.\.venv\Scripts\python -B -m compileall src scripts -q
.\.venv\Scripts\python -B -m scripts.project_snapshot
.\.venv\Scripts\python -B -m scripts.check_repo_guardrails
.\.venv\Scripts\python -B -m scripts.check_architecture_guardrails
.\.venv\Scripts\python -B -m scripts.repo_inventory
.\.venv\Scripts\python -B -m scripts.import_graph
.\.venv\Scripts\python -B -m scripts.check_ocr_backend --backend surya
.\.venv\Scripts\python -B -m scripts.check_extractor
.\.venv\Scripts\python -B -m pytest -p no:cacheprovider
git diff --check
git status --short
```

## Test Interpretation

Synthetic passing tests mean the repo contracts still execute. They do not mean the OCR/extraction quality is acceptable on real court PDFs.

## TOOLKIT-1 Verification Commands

```powershell
.\.venv\Scripts\python -B -m scripts.check_gold_manifest --gold tests\fixtures\gold_manifest_synthetic.jsonl
.\.venv\Scripts\python -B -m scripts.evaluate_gold_manifest --gold tests\fixtures\gold_manifest_synthetic.jsonl --predictions tests\fixtures\prediction_manifest_synthetic.jsonl
.\.venv\Scripts\python -B -m pytest -p no:cacheprovider
```

TOOLKIT-1 chưa có OCR CER/WER và không được dùng để kết luận real quality từ synthetic fixture.
## Surya runtime va stamp suppression

Synthetic tests cover Docker resolver override, Windows Docker Desktop discovery, diagnostics khong GPU mac dinh, stamp mask/suppression, protected dark text, post-OCR filter, raw/filtered/excluded artifacts va preprocessed OCR path. Passing tests khong thay the visual review OCR that tren Ezycloudx.
