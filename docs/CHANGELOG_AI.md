# AI Changelog

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
