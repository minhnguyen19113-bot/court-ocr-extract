# AI Changelog

## 2026-07-10 - Pin Surya OCR Version

- Pin `surya-ocr==0.20.0` trong `pyproject.toml` và `requirements.txt`.
- Thêm version guard trước import/API/runtime; 0.21.x báo Surya 2/Docker và reinstall instructions.
- Nâng `scripts.check_ocr_backend` để in installed/supported version mà không inference.
- Thêm tests cho supported, drifted, missing và no-inference paths.
- Không chạy PDF/OCR/Surya inference/LLM/cloud/full pipeline.

## 2026-07-10 - OCR Uses Preprocessed Input

- Xác nhận Surya trước đây dùng rendered original, không dùng output từ `debug-preprocess`.
- Thêm opt-in `--use-preprocessed` và preprocess options cho `debug-ocr-review`/`ocr`.
- Nối final preprocessed path vào Surya; giữ rendered-original behavior khi không có flag.
- Thêm OCR input source/options vào result/cache/manifest và giữ preprocess/OCR artifacts cạnh nhau.
- Thêm fake Surya/CLI tests; không chạy PDF/OCR/LLM/cloud/full pipeline thật.

## 2026-07-10 - Red Seal + Text Enhancement Fix

- Mở rộng red mask thành HSV + Lab + RGB, morphology, component count và residual metrics.
- Thêm `neutralize`, `inpaint`, `white_fill` cùng black-text protection/overlap warning.
- Thêm `text-enhance off|light|medium|strong`, staged artifact và dark/foreground guard.
- Nâng CLI/debug HTML với protection mask, text-enhanced image và metadata mới.
- Thêm synthetic tests; giữ nguyên deskew và không chạy PDF/OCR/Surya/LLM/cloud/full pipeline thật.

## 2026-07-10 - Preprocess Safety Fix

- Thay auto-deskew mặc định bằng `off`; thêm `safe`/`force` và metadata angle/confidence/reason.
- Chuyển red seal HSV detection/removal lên ảnh màu trước grayscale; thêm mask, ratio và high-ratio safeguard.
- Thêm foreground/dark/brightness/entropy blank guard cùng fallback original/previous safe stage.
- Nâng `debug-preprocess` HTML/CLI với artifacts, metadata, warnings và ba preprocess profiles.
- Thêm synthetic tests; không đọc/chạy PDF thật, OCR/Surya/model/cloud hoặc full pipeline.

## 2026-07-10 - TOOLKIT-1 Evaluation Harness + Gold Dataset Manifest

- Thêm `evaluation/manifest.py`, `metrics.py`, `report.py`, `privacy.py` và package exports.
- Thêm schema validation nhẹ cho gold/prediction JSONL cùng duplicate case/obvious PII checks.
- Implement OCR, section, field, participant, evidence, source reference, review và warning metrics.
- Thêm safe JSON/Markdown report whitelist chỉ numeric metrics.
- Thêm `scripts.check_gold_manifest` và `scripts.evaluate_gold_manifest` với required paths, không real-data default.
- Thêm synthetic redacted gold/prediction fixtures và tests cho valid/mismatch/PII/report/CLI behavior.
- Mở rộng guardrail cho `data_private/`, `data/gold/`, manifest ngoài tests và PII trong fixture.
- Không tạo/đọc gold thật, không chạy PDF/OCR/Excel thật, không gọi model/cloud, không commit/push.

## 2026-07-10 - Phase 1F Consolidate Duplicate Extraction Modules

- Chọn `src/court_ocr_extract/extraction_pipeline.py` và `src/court_ocr_extract/extractors/` làm canonical extraction path.
- Hợp nhất Local LLM backend cùng typed compatibility adapter vào `extractors/local_llm_extractor.py`.
- Hợp nhất rule backend/typed anchor vào `extractors/rule_support.py`; chuyển regex parser vào `extractors/rule_parser.py`.
- Migrate pipeline, remote worker, runtime script, và tests sang canonical imports.
- Xóa `extraction/base.py`, `extraction/local_llm_extractor.py`, `extraction/rule_support.py`, root `extractor.py`, và root `llm.py`.
- Giữ typed merge/schema/validation/GLiNER helpers và direct vision/cloud benchmark adapters đúng vai trò riêng.
- Sửa `scripts.check_extractor` thành static configuration check mặc định, không endpoint request.
- Thêm synthetic no-network extraction contract tests và architecture guardrails.
- Không chạy PDF/dữ liệu/model endpoint thật, không gọi cloud API, không sửa prompt/schema lớn, và không push.

## 2026-07-10 - Phase 1E Consolidate Duplicate Excel / Export Paths

- Audited Excel/export filenames, imports, docs references, import graph, và safe repo inventory.
- Giữ `src/court_ocr_extract/excel_writer.py` làm canonical Excel writer duy nhất.
- Chuyển `rows_from_result()` và `write_excel_from_results()` từ duplicate writer vào canonical module.
- Chuyển pipeline, evaluation script, và tests sang canonical import path.
- Xóa `src/court_ocr_extract/excel.py` và `src/court_ocr_extract/export/excel_writer.py`; restore path là Git history trước Phase 1E.
- Thêm synthetic workbook contract tests cho draft records và typed `ExtractionResult`.
- Cập nhật architecture guardrail để fail khi canonical writer thiếu hoặc legacy Excel import quay lại.
- Không thay đổi 11 domain headers; 8 audit/trace columns mục tiêu vẫn cần phase schema riêng.
- Không chạy PDF thật, không đọc dữ liệu thật/Excel thật, không gọi cloud API, và không push.

## 2026-07-09 - Phase 1D Old App Folders Cleanup

- Audited old app references with `scripts.import_graph`, `scripts.repo_inventory`, and `git grep`.
- Confirmed the main `src/court_ocr_extract`/CLI path does not import `app/`, `app_fastapi/`, or `app_streamlit/`.
- Removed old app folders: `app/`, `app_fastapi/`, and `app_streamlit/`.
- Removed stale old app launch/doc/template artifacts: `scripts/ezycloudx_run_api.sh`, `scripts/ezycloudx_run_api_windows.ps1`, `docs/streamlit_vs_fastapi.md`, and `templates/upload.html`.
- Removed old UI-only optional dependencies `streamlit` and `jinja2`; kept FastAPI/uvicorn dependencies for supported remote worker tooling.
- Updated architecture guardrails/tests so old app run instructions in README/docs/scripts fail.
- Updated repo memory/docs for restore path: use Git history before Phase 1D if old UI code is needed.
- Did not run real PDFs, inspect real data, call cloud APIs, or modify Surya OCR, Local LLM extractor, Excel writer, or VLM benchmark modules.

## 2026-07-08 - Phase 1C Architecture Audit + Production Toolkit

- Thêm `scripts/repo_inventory.py` để tạo inventory an toàn, bỏ qua protected real-data/output roots.
- Thêm `scripts/import_graph.py` để dựng import graph bằng `ast` cho `src/`, `scripts/`, và `tests/`.
- Thêm `scripts/check_architecture_guardrails.py` để kiểm default/main path, cloud disabled defaults, protected path policy, CLI full-document support, và duplicate/legacy warnings.
- Thêm tests cho architecture audit scripts.
- Thêm docs Phase 1C: `REPO_INVENTORY`, `IMPORT_GRAPH`, `LEGACY_ARCHIVE_PLAN`, `PRODUCTION_TOOLKIT`, `EVALUATION_PLAN`, `GOLD_DATASET_GUIDE`, `PRIVACY_REDACTION_PLAN`, `OBSERVABILITY_PLAN`, và `MLOPS_PLAN`.
- Cập nhật `AGENTS.md`, `AGENT_ROLES.md`, `TESTING.md`, `CLEANUP_PLAN.md`, `PROJECT_STATE.md`, `TASKS.md`, `DECISIONS.md`, và `CODEX_HANDOFF.md`.
- Không xóa file, không archive/mass-move tracked code, không chạy PDF thật, không đọc dữ liệu thật, không gọi cloud API.
- Không push vì Phase 1C chưa yêu cầu push.

## 2026-07-08 - Repo Cleanup Audit

- Dọn generated cache local trong workspace, gồm `__pycache__/` và `.pytest_cache/`.
- Xác nhận không có cache Python tracked trong Git.
- Giữ nguyên tracked legacy/duplicate modules vì chưa có bằng chứng an toàn để xóa mà không ảnh hưởng pipeline.
- Không inspect hoặc dọn `data/`, `outputs/`, `logs/`, `work/`, PDF thật, image thật, Excel thật, hoặc artifact real-data.
- `ruff` không chạy được vì package chưa được cài trong `.venv`.

## 2026-07-07 - Sửa giới hạn trang debug/full-document

- Sửa `parse_page_range()` để `None`, chuỗi rỗng, và `all` nghĩa là toàn bộ trang; không còn default 3 trang đầu.
- Sửa default `--pages` của debug render/preprocess/red-seal thành toàn bộ trang; muốn giới hạn phải truyền rõ `--pages 1-3`.
- Thêm `--full-document` và `--max-pages` cho `debug-ocr-review` và `ocr`.
- `debug-ocr-review --full-document` và `ocr --full-document` truyền `max_pages=None`, `stop_marker=""`.
- Sửa Surya OCR để `stop_marker=""` không gọi marker detector, không truncate text, không break sớm, và không warning marker missing.
- Thêm test synthetic cho page range, CLI full-document, Surya full-document marker behavior, và no-fallback guard.
- Không chạy PDF thật, không inspect dữ liệu thật, không chạy extraction/LLM/Excel.

## 2026-07-07 - Phase 2A Surya OCR Runtime + Visual OCR Review

- Triển khai code path `SuryaOCRBackend` cho rendered images và output `OCRResult/OCRPage`.
- Thay placeholder runtime bằng flow thật `ocr_pdf_prefix()` -> `render_pdf_pages()` -> Surya OCR trên image -> `OCRResult`.
- Thêm kiểm tra Surya import/version/API availability có install hints.
- Hỗ trợ API `surya-ocr 0.20.0` qua `RecognitionPredictor(..., full_page=True)`.
- Nếu API Surya cài đặt không nhận diện được, adapter raise lỗi rõ: `Surya package is installed but this adapter does not support the installed API. Detected ...`.
- Thêm chuẩn hóa line với `line_id`, bbox, confidence, reading order, và warnings.
- Sắp xếp combined text theo `reading_order` khi Surya trả về thứ tự đọc.
- Thêm Surya page artifacts: original image, bbox overlay, line JSON, page text markdown, combined text, manifest, và HTML index.
- Nâng cấp OCR review HTML với original image, bbox overlay, line table, artifact links, và warnings.
- Thêm test synthetic/mocking cho `ocr_pdf_prefix()`, Surya OCR contract, placeholder guard, no-Tesseract fallback guard, và visual review.
- Không chạy PDF thật.
- Không inspect artifact OCR/debug/output thật.
- Không gọi cloud API.
- Không sửa Local LLM extractor hoặc Excel writer.

## 2026-07-07 - Cập nhật quy tắc ngôn ngữ

- Thêm quy tắc báo cáo tiếng Việt vào `AGENTS.md`.
- Thêm template `# BÁO CÁO TASK` với 9 mục tiếng Việt.
- Đồng bộ `PROJECT_STATE`, `DECISIONS`, `CODEX_HANDOFF`, `AGENT_ROLES`, và `TASKS` để các phiên Codex sau dùng tiếng Việt trong report.
- Không sửa pipeline code.
- Không xóa file.
- Không chạy hoặc đọc dữ liệu thật.

## 2026-07-07 - Phase 1B Clean Main Defaults

- Cleaned README, Ezycloudx setup/runbook docs, visual QA guide, workflow docs, `.env.example`, and sample/full run scripts away from Tesseract defaults.
- Set `settings.py` defaults to Surya OCR target, local vLLM Qwen2.5-14B target, and local VLM benchmark target.
- Added `surya` as the supported backend name for the existing Surya wrapper while keeping old `surya_optional` compatibility.
- Marked `config.py` as legacy/compatibility config.
- Recorded `excel_writer.py` as canonical Excel writer.
- Updated cleanup plan, architecture, testing, runbook, project state, decisions, tasks, and handoff.
- No real PDFs, OCR text, derived real-data outputs, or sensitive artifacts were inspected.
- No files were deleted or moved into archive.
- No real Surya/VLM runtime implementation was added.

## 2026-07-07 - Phase 1A Reorientation

- Added project memory files for state, architecture, decisions, tasks, handoff, pipeline spec, data schema, debug output spec, testing, model benchmark, Ezycloudx runbook, security/privacy, cleanup plan, and agent roles.
- Updated `AGENTS.md` with the new rebuild direction, Codex memory protocol, and cleanup approval rule.
- Added safe repo snapshot and guardrail check scripts.
- Added focused tests for the new guardrail/snapshot helpers.
- No real PDFs, OCR text, derived real-data outputs, or sensitive artifacts were inspected.
- No production pipeline behavior was intentionally changed.
- No files were deleted.
## 2026-07-10 - SURYA WINDOWS RUNTIME + OCR STAMP SUPPRESSION V3

- Them resolver Docker runtime cho Windows va script diagnostics Surya.
- Them stamp suppression/filter theo mask, overlap metadata, raw/filtered/excluded artifacts.
- Sua relative link trong OCR review khi artifact nam ngoai `ocr_surya/`.
- Bo sung synthetic tests; khong chay du lieu/PDF/OCR inference that.
## 2026-07-13 - PRE-CONTENT EXTRACTION A/B TEST

- Thêm nhánh thử nghiệm so sánh hybrid rule+LLM và LLM-only trên phần trước `NỘI DUNG VỤ ÁN`.
- Thêm document router, segmenter, schema, rule extractor, hybrid merge, prompts và compare runner.
- Thêm review artifacts JSON/Excel/HTML và synthetic tests; không chạy PDF/Surya/Local LLM thật trong Codex.
