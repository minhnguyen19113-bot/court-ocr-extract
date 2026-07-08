# Project State

Last updated: 2026-07-08

## Current Phase

Phase 2A: SURYA OCR RUNTIME + VISUAL OCR REVIEW.

Phase này triển khai đường chạy `SuryaOCRBackend` ở mức code/contract và thêm artifact để review OCR bằng hình ảnh. Codex không chạy PDF thật, không gọi cloud API, và chưa chứng minh chất lượng OCR trên dữ liệu thật.

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
- `src/court_ocr_extract/excel_writer.py` is canonical Excel writer for new rebuild work.
- Excel writers, extractors, validation modules, and PDF/render modules have duplicate or overlapping implementations.
- Existing tests are contract/control-flow oriented and use synthetic fixtures only.

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

## Next Gate

Project Owner / ChatGPT nên kiểm tra Surya runtime trên Ezycloudx trước, sau đó quyết định Phase 2B sẽ ưu tiên cải thiện visual QA, pin version `surya-ocr`, hay chuyển sang hardening Local LLM extraction.
