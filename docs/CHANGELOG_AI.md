# AI Changelog

## 2026-07-07 - Phase 2A Surya OCR Runtime + Visual OCR Review

- Triển khai code path `SuryaOCRBackend` cho rendered images và output `OCRResult/OCRPage`.
- Thêm kiểm tra Surya import/version availability có install hints.
- Thêm chuẩn hóa line với `line_id`, bbox, confidence, reading order, và warnings.
- Thêm Surya page artifacts: original image, bbox overlay, line JSON, page text markdown, combined text, manifest, và HTML index.
- Nâng cấp OCR review HTML với original image, bbox overlay, line table, artifact links, và warnings.
- Thêm test synthetic/mocking cho Surya OCR contract và visual review.
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
