# Testing

## Front/Decision Source và Legal Relationship Tests

Mười một modules bắt buộc kiểm source allowlist, middle exclusion, quoted/unquoted explicit verdict, multi-defendant mapping, no-statute inference, defendant-specific relationship, non-defendant case relationship, ambiguous mapping, same-person/different-role rows, workbook/HTML source audit và no-full-document fallback. Integrated fixture có ba front defendants, một victim, hai charges, một người có hai role và misleading middle charge text; toàn bộ là synthetic.

Reverse scan test còn buộc `max_scan_pages` dương/hữu hạn. Charge evidence hợp lệ phải là `decision_tail`; middle evidence không được vào final relationship. Full suite sau task: 242/242 passed, một warning deprecation từ dependency Surya/Pydantic. Kết quả này chỉ chứng minh schema/control-flow, không chứng minh chất lượng OCR/extraction thật.

## Final Role, Boundary và Decision Tail Tests

Mười hai modules bắt buộc kiểm marker page 4/8, fallback khi thiếu marker, trial-panel isolation, embedded defendant intro, strong identity validator, nhiều metadata anchors cùng dòng, acceptance-date binding, primary role allowlist, other-participant sheet, safe multi-person split, role-aware dedupe, blank criminal relationship, reverse tail scan và explicit charge phrases. `test_decision_tail_reverse_scan.py` còn khóa CLI không chấp nhận Tesseract/backend khác.

Tất cả input là OCR lines, cache records, page objects hoặc text synthetic; reverse scan dùng fake callable. Không test nào mở PDF thật, đọc cache/output thật, gọi Surya/LLM/Docker/cloud hoặc dùng allowlist tên người/file/page của một case thật.

Focused regression sau hardening: 8/8 passed. Full suite cuối task: 226/226 passed; warning duy nhất là Pydantic deprecation từ dependency `surya`.

## Final Excel schema tests

Năm modules `test_final_excel_*.py` kiểm đúng 14 cột/thứ tự, final row builder, cấu trúc synthetic 6 defendant + 4 participant, sheet đầu `FINAL_EXCEL`, không có cột thừa, HTML preview đứng trước debug, rule-only/rule-then strategy và missing-data notes. Fixtures chỉ dùng identity/case/address synthetic; không đọc PDF/cache/Excel/output thật và không gọi LLM/Surya/Docker/cloud.

Kết quả full suite sau realignment: 199/199 test passed; có một warning deprecation từ dependency `surya`/Pydantic, không có test failure.

## Rule anchor và per-block LLM tests

Mười một test modules `test_rule_anchor_*.py` với 23 cases dùng OCR-line dictionaries/OCR cache synthetic và fake callable. Coverage gồm exact metadata number tokens sau header dài, judgment number/date adjacency, OCR typo, QĐXX exclusion, single/multi defendant, page-number warning severity, one-line/newline panel, hierarchical participant numbering/inline roles, defendant spouse/children/address continuation, validators, document routing, strategy defaults, LLM cap và Excel/HTML artifacts. Tests không đọc PDF/cache thật và không gọi Surya, Docker, Local LLM hoặc cloud.

## Local LLM budget/chunk/report tests

- `test_llm_preflight.py`: `/models`, chat nhỏ và connection refused bằng fake opener.
- `test_llm_context_budget.py`: trim trước request, inequality budget, `max_tokens>0` và context error taxonomy.
- `test_llm_chunked_extraction.py`: nhiều defendant, partial success và chunk warning.
- `test_compare_requires_llm.py`: fail-fast và không tạo null result giả; hybrid giữ rule output.
- `test_structured_excel_export.py`, `test_llm_status_reporting.py`: review sheets không chứa JSON blob, `LLM_STATUS` và HTML runtime metadata.
- Không test nào gọi vLLM/Docker/Surya/PDF/cloud thật.

## Marker early-stop tests

- `tests/test_marker_detection.py`: exact, no-diacritic, noisy spacing, split/filtered-only, truncated/low-confidence và same-page trim.
- `tests/test_ocr_marker_early_stop.py`: predictor runner tạo một lần, stop page 3, marker-missing full scan và full-document override.
- `tests/test_ocr_cache_marker_metadata.py`: cache round-trip và HTML summary/highlight.
- `tests/test_pre_content_uses_text_before_marker.py`: extraction không nhận full OCR text khi cache có `text_before_marker`.
- Toàn bộ test dùng synthetic images/lines và monkeypatch, không gọi PDF/Surya/Docker thật.

## Surya runtime tests

- `tests/test_surya_runtime_backend_check.py` kiểm GPU flag, success/failure và subprocess timeout bằng monkeypatch.
- `tests/test_surya_runtime_preflight_cli.py` kiểm Docker binary override, thứ tự preflight và predictor không chạy khi preflight fail.
- `tests/test_surya_runtime_no_hang_diagnostics.py` kiểm `last_stage` và `SuryaRuntimeError` khi startup timeout.
- Unit suite không được gọi Docker server, GPU container hoặc Surya inference thật.

Last updated: 2026-07-17

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
## Pre-content legacy và rule-anchor synthetic tests

Tests legacy vẫn kiểm `hybrid_rule_llm`/`llm_only` khi truyền strategy rõ. Default tests kiểm `rule_anchor_only,rule_then_llm_per_block`, anchor boundaries, structured rows, runtime status và không tạo fake output khi LLM unavailable.
## Stamp object erase synthetic tests

Tests tạo ảnh/mask synthetic trong `tmp_path`: dấu đỏ có residual xám, red mask một phần, stamp overlap chữ đen, blank page và red noise nhỏ. Assertions kiểm object mask rộng hơn red mask, white-fill giảm residual hơn mask-only, overlap warning bảo toàn chữ và artifacts tồn tại. Passing tests không chứng minh threshold phù hợp với scan thật.
## Final candidate selection synthetic tests

Tests cover disconnected horizontal stamp, horizontal stamp cùng side seal, object union seed, chọn `stamp_object_erased`, loại text-enhanced residual amplification, loại blank candidate và bảo toàn overlap-text fallback. Passing tests chỉ xác nhận scoring/control flow synthetic, chưa xác nhận threshold trên scan thật.
