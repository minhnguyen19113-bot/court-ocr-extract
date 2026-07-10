# Project State

Last updated: 2026-07-10

## Current Phase

OCR USES PREPROCESSED INPUT sau RED SEAL + TEXT ENHANCEMENT FIX.

Task này nối final preprocessed image vào Surya OCR theo opt-in CLI và Mode 3 do Project Owner chọn. Codex chỉ dùng fake backend/synthetic images, không đọc/chạy PDF thật, không gọi Surya/Local LLM/cloud và không chạy full pipeline.

## Active Direction

The rebuild has two approved candidate paths:

1. Main candidate: PDF render -> optional preprocess -> Surya OCR -> OCR cache -> normalize/split -> rule extraction for easy fields -> local LLM extraction for hard fields -> evidence validation -> Excel -> QA report -> debug UI/human review.
2. Benchmark path: page image -> local VLM end-to-end extraction -> validation -> Excel -> QA report -> debug UI/human review.

Tesseract is legacy only. PaddleOCR is not part of the rebuild path. Cloud OCR/extraction adapters are disabled by default and may only be used for explicit opt-in benchmarks.

## Quy tắc ngôn ngữ

- Báo cáo gửi Project Owner/ChatGPT phải viết bằng tiếng Việt.
- Heading report ưu tiên tiếng Việt.
- Tên kỹ thuật như file path, class, function, CLI command, env var, model name, package name, schema field được giữ nguyên tiếng Anh.
- Không dùng report nửa Anh nửa Việt.
- Nếu prompt từ ChatGPT có heading tiếng Anh, Codex vẫn trả lời bằng template tiếng Việt trừ khi được yêu cầu khác.
- Project memory docs ưu tiên tiếng Việt trong các cập nhật mới.

## Current Repo Facts

- Surya đã có đường chạy backend ở mức code/contract, nhưng các adapter legacy chưa được hợp nhất toàn bộ và chất lượng OCR thật chưa được Project Owner xác nhận.
- VLM modules and synthetic smoke tests exist and should be treated as experimental benchmark assets.
- README, Ezycloudx docs, visual QA docs, run scripts, `.env.example`, and `settings.py` now point to the Surya target/default instead of Tesseract.
- `src/court_ocr_extract/settings.py` is canonical config for new rebuild work.
- `src/court_ocr_extract/config.py` remains a legacy compatibility module for older imports.
- `src/court_ocr_extract/excel_writer.py` là Excel writer canonical duy nhất; `excel.py` và `export/excel_writer.py` đã được xóa trong Phase 1E sau khi migrate caller.
- Extraction backend overlap đã được xử lý trong Phase 1F; validation modules, Surya adapters, và PDF/render modules vẫn có implementation chồng lấn.
- Evaluation harness chỉ đọc JSONL path được truyền rõ; report chỉ chứa aggregate numeric metrics, không chứa raw expected/predicted values.
- Existing tests are contract/control-flow oriented and use synthetic fixtures only.
- Old app folders `app/`, `app_fastapi/`, and `app_streamlit/` were removed in Phase 1D. Restore path: use Git history before the Phase 1D commit if needed.

## Safety Boundary

Codex may inspect code, config, docs, prompts, and synthetic tests/fixtures. Codex must not inspect real PDFs, real OCR text, real rendered images, real Excel outputs, real debug outputs, or real logs that may contain sensitive data.

## Latest Phase 1B Work

- Cleaned README, `.env.example`, Ezycloudx docs, visual QA docs, workflow docs, and run scripts away from Tesseract defaults.
- Changed `settings.py` default OCR backend to `surya` and enabled Surya target config by default.
- Added `surya` as a supported alias for the existing Surya OCR backend wrapper.
- Marked `config.py` as compatibility/legacy and `excel_writer.py` as canonical in docs.
- Updated cleanup plan and project memory for Phase 1B.
- Did not delete files.
- Did not implement real Surya or VLM runtime.
- Did not read real data artifacts.

## Latest Memory-Only Update

- Added project-wide Vietnamese language/reporting rule.
- Added standard Vietnamese task report template.
- Did not change pipeline code.
- Did not delete files.
- Did not run or inspect real data.

## Latest Phase 2A Work

- Triển khai routing `SuryaOCRBackend` cho backend `surya` ở mức code/contract.
- Thêm kiểm tra import/version/API Surya có hướng dẫn cài đặt khi thiếu runtime.
- Adapter hiện hỗ trợ API `surya-ocr 0.20.0` qua `RecognitionPredictor(..., full_page=True)` và báo lỗi rõ nếu API cài đặt không được hỗ trợ.
- Thêm đường render PDF thành image trước khi gọi Surya OCR backend.
- Chuẩn hóa output line của Surya vào `OCRPage.lines` với `line_id`, `text`, `bbox`, `confidence`, `reading_order`, và `warnings`.
- Thêm artifact theo từng page để review Surya OCR: ảnh gốc, bbox overlay, line JSON, page text markdown, combined text, manifest, và HTML index.
- Nâng cấp OCR review HTML để hiển thị ảnh gốc, bbox overlay, line table, warnings, và link đến artifact từng page.
- Thêm test synthetic/mocking cho `ocr_pdf_prefix()`, contract Surya, placeholder guard, no-Tesseract fallback guard, và visual review.
- `src/court_ocr_extract/ocr_backends/surya_ocr.py` không còn placeholder `runtime wiring is incomplete`.
- Không chạy PDF thật và không inspect output thật.
- Chất lượng OCR thật phải do Project Owner đánh giá trên Ezycloudx.

## Latest Full-Document Debug Fix

- `parse_page_range(None)`, `parse_page_range("")`, và `parse_page_range("all")` trả `None`, nghĩa là toàn bộ trang.
- `debug-render`, `debug-preprocess`, và `debug-red-seal` mặc định chạy toàn bộ trang khi không truyền `--pages`.
- `debug-ocr-review` và `ocr` có `--full-document` để truyền `max_pages=None`, `stop_marker=""`.
- Surya OCR không còn dừng/truncate tại marker `NỘI DUNG VỤ ÁN` khi `stop_marker=""`.
- Thêm test synthetic cho page range, CLI full-document, và Surya full-document behavior.
- Không chạy PDF thật, không đọc dữ liệu thật, không chạy extraction/LLM/Excel.

## Latest Repo Cleanup

- Dọn generated cache local như `__pycache__/` và `.pytest_cache/` trong workspace.
- Không xóa tracked source/docs legacy vì `docs/CLEANUP_PLAN.md` vẫn phân loại chúng là `legacy_optional`, `duplicate_conflict`, `experimental`, hoặc `unknown_need_review`.
- Không inspect hoặc dọn `data/`, `outputs/`, `logs/`, `work/`, model files, PDF thật, Excel thật, image thật.
- `ruff` không chạy được vì chưa được cài trong `.venv`.

## Latest Phase 1C Work

- Thêm `scripts/repo_inventory.py` để tạo inventory an toàn, bỏ qua protected real-data/output roots.
- Thêm `scripts/import_graph.py` để dựng import graph bằng `ast` cho `src/`, `scripts/`, và `tests/`.
- Thêm `scripts/check_architecture_guardrails.py` để kiểm Surya/main defaults, cloud disabled defaults, protected path policy, CLI full-document behavior, và duplicate/legacy warnings.
- Thêm test synthetic/contract cho các script architecture audit mới.
- Thêm docs Phase 1C: `REPO_INVENTORY`, `IMPORT_GRAPH`, `LEGACY_ARCHIVE_PLAN`, `PRODUCTION_TOOLKIT`, `EVALUATION_PLAN`, `GOLD_DATASET_GUIDE`, `PRIVACY_REDACTION_PLAN`, `OBSERVABILITY_PLAN`, và `MLOPS_PLAN`.
- Cập nhật `AGENTS.md`, `AGENT_ROLES.md`, `TESTING.md`, `CLEANUP_PLAN.md`, `DECISIONS.md`, `TASKS.md`, `CHANGELOG_AI.md`, và `CODEX_HANDOFF.md`.
- Không xóa file, không chạy dữ liệu thật, không inspect protected artifacts, không push.

## Latest Phase 1D Work

- Audited old app references with `scripts.import_graph`, `scripts.repo_inventory`, and `git grep`.
- Confirmed `src/court_ocr_extract` and CLI main path do not import `app/`, `app_fastapi/`, or `app_streamlit/`.
- Removed old app folders: `app/`, `app_fastapi/`, and `app_streamlit/`.
- Removed stale old app artifacts: `docs/streamlit_vs_fastapi.md`, `scripts/ezycloudx_run_api.sh`, `scripts/ezycloudx_run_api_windows.ps1`, and `templates/upload.html`.
- Removed old UI-only optional dependencies `streamlit` and `jinja2`; kept `fastapi`, `uvicorn`, and `python-multipart` for supported remote worker tooling.
- Updated architecture guardrails to fail if README/docs/scripts reintroduce old app run instructions.
- Did not touch Surya OCR backend, Local LLM extractor, Excel writer, VLM benchmark modules, or protected real-data paths.

## Latest Phase 1E Work

- Hợp nhất `rows_from_result()` và `write_excel_from_results()` vào canonical `src/court_ocr_extract/excel_writer.py`.
- Chuyển pipeline, evaluation script, và tests khỏi `court_ocr_extract.excel`/`court_ocr_extract.export.excel_writer` sang canonical module.
- Xóa `src/court_ocr_extract/excel.py` và `src/court_ocr_extract/export/excel_writer.py`; restore bằng Git history trước Phase 1E nếu cần.
- Giữ nguyên 11 domain headers và hai workbook contract hiện hữu: draft records dùng `DATA` + `RUN_SUMMARY`, typed `ExtractionResult` dùng `Trich xuat`.
- Thêm synthetic workbook contract tests và architecture guardrail cho canonical path/legacy imports.
- Các cột audit/trace mục tiêu chưa được thêm trong phase này; cần một phase schema riêng nếu Project Owner duyệt.
- Không chạy PDF thật, không đọc Excel thật, không gọi cloud API, và không push.

## Latest Phase 1F Work

- Chọn `src/court_ocr_extract/extraction_pipeline.py` làm canonical orchestrator và `src/court_ocr_extract/extractors/` làm canonical backend package.
- Hợp nhất Local LLM backend/typed adapter vào `extractors/local_llm_extractor.py`; hợp nhất rule backend/typed anchor vào `extractors/rule_support.py`.
- Chuyển rule parser vào `extractors/rule_parser.py` và migrate pipeline, remote worker, scripts, tests sang canonical imports.
- Xóa `extraction/base.py`, `extraction/local_llm_extractor.py`, `extraction/rule_support.py`, root `extractor.py`, và root `llm.py`; restore bằng Git history trước Phase 1F nếu cần.
- Giữ `extraction/merge.py`, `schemas.py`, `validators.py`, và `gliner_extractor.py` vì có trách nhiệm typed merge/schema/validation/experimental riêng.
- `scripts.check_extractor` mặc định chạy static configuration check, không gọi endpoint.
- Thêm synthetic extraction contract tests với fake response; không network/model thật.

## Latest TOOLKIT-1 Work

- Thêm `src/court_ocr_extract/evaluation/` gồm manifest validation, privacy/hash/redaction, metrics và safe report.
- Thêm gold/prediction JSONL synthetic fixtures trong `tests/fixtures/`; gold thật vẫn nằm ngoài Git/Codex.
- Thêm `scripts.check_gold_manifest` và `scripts.evaluate_gold_manifest`; không có default path vào `data/` hoặc `outputs/`.
- Implement OCR, field, participant, evidence, source reference, review và warning aggregate metrics.
- Guardrail bảo vệ `data_private/`, `data/gold/`, manifest ngoài tests và obvious PII trong synthetic manifests.
- Synthetic evaluation không chứng minh chất lượng OCR/extraction thật và không thay human review.

## Latest Preprocess Safety Fix

- `debug-preprocess` có `--deskew off|safe|force`, `--red-seal-removal on|off` và `--preprocess-profile conservative|balanced|aggressive`.
- Default an toàn là `deskew=off`, red-seal removal bật và profile conservative.
- HSV red mask/removal chạy trên original color trước grayscale; ratio quá cao sẽ skip thay vì xóa mạo hiểm.
- Safe deskew cần đủ horizontal evidence, góc 0.3-5 độ, không có foreground sát mép và không có layout hai cột mơ hồ.
- Blank guard so foreground/dark ratio/brightness/entropy và fallback original hoặc `seal_removed` khi after mất nội dung.
- Debug review hiển thị original, red mask, seal removed, final, compare, metadata và warnings theo page.
- Tests chỉ dùng ảnh synthetic; chất lượng và ngưỡng trên scan thật chưa được xác nhận.

## Latest Red Seal + Text Enhancement Fix

- Red detector kết hợp HSV + Lab + RGB, morphology cleanup, component count và residual estimate.
- Thêm `neutralize`, `inpaint`, `white_fill`; default `neutralize`, còn `inpaint` có residual second pass.
- Thêm `black_text_protection_mask`, overlap ratio và warning `red_mask_overlaps_dark_text`.
- Thêm `text_enhance=off|light|medium|strong`; default `light`, chạy sau red removal.
- Text guard phát hiện foreground loss/dark-pixel explosion/entropy collapse và fallback stage an toàn.
- Debug per-page có red mask, protection mask, seal removed, text enhanced, final và metadata đầy đủ.
- Deskew logic/default giữ nguyên; tests chỉ dùng synthetic images.

## Latest OCR Uses Preprocessed Input

- Trước task này, Surya luôn nhận rendered original; `debug-preprocess` là nhánh review độc lập.
- `debug-ocr-review` và `ocr` có `--use-preprocessed` cùng toàn bộ preprocess options.
- Khi opt-in, backend truyền final preprocessed path vào Surya và lưu preprocess + OCR input artifacts cạnh nhau.
- `OCRResult.metadata`, OCR cache và Surya manifest ghi `ocr_input_source` cùng Mode 3 options.
- Không có flag thì behavior cũ và `ocr_input_source=rendered_original` được giữ nguyên.
- Preprocess exception tạo named final safe copy và warning, không âm thầm gọi OCR bằng rendered path.
- Tests dùng fake Surya; chưa có real PDF/OCR inference trong Codex.

## Next Gate

Project Owner cần chạy `debug-ocr-review --use-preprocessed` Mode 3 trên VM và so sánh OCR text/bbox với image input. Chỉ sau visual OCR review mới quyết định bật Mode 3 cho pilot mặc định.
