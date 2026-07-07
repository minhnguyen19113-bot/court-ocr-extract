# Project State

Last updated: 2026-07-07

## Current Phase

Phase 1B: CLEAN MAIN DEFAULTS + CANONICAL CONFIG.

This phase cleaned main/default docs/config/scripts away from Tesseract, selected canonical config/writer decisions, and kept legacy code in place for later review. It does not implement real Surya runtime, real VLM runtime, production extraction changes, real-data pilots, or file deletion.

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

- Surya appears in dependencies and multiple modules, but the approved Surya main path is not yet fully consolidated or runtime-complete.
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

## Next Gate

Project Owner / ChatGPT should review remaining duplicate modules before Phase 1C/2: extraction packages, Excel duplicates, app folders, Surya adapter consolidation, debug UI parity, and Local LLM strictness.
