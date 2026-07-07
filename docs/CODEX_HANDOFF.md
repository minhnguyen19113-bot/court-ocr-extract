# Codex Handoff

Last updated: 2026-07-07

## Read First

For the next Codex session, read these before acting:

1. `AGENTS.md`
2. `docs/PROJECT_STATE.md`
3. `docs/DECISIONS.md`
4. `docs/TASKS.md`
5. `docs/CODEX_HANDOFF.md`
6. `docs/ARCHITECTURE.md`
7. `docs/PIPELINE_SPEC.md`
8. `docs/CLEANUP_PLAN.md` if cleanup/refactor is involved

## Current State

Phase 1B cleaned main defaults and canonical decisions. README, `.env.example`, Ezycloudx docs, visual QA docs, workflow docs, run scripts, and `settings.py` now point to Surya target defaults instead of Tesseract defaults.

Canonical decisions:

- `src/court_ocr_extract/settings.py` is canonical rebuild config.
- `src/court_ocr_extract/config.py` is compatibility/legacy.
- `src/court_ocr_extract/excel_writer.py` is canonical Excel writer.
- Surya OCR + local LLM is the main candidate.
- Local VLM is the benchmark path.

Phase 1B has not implemented real Surya, real VLM, production extraction changes, or any deletion.

## Important Warnings

- Do not inspect real data directories or outputs.
- Do not run real PDF workflows inside Codex.
- Do not call cloud APIs by default.
- Do not use synthetic smoke to judge real quality.
- Do not clean/delete/archive files until Phase 1B scope is approved.

## Quy tắc ngôn ngữ

- Báo cáo gửi Project Owner/ChatGPT phải viết bằng tiếng Việt.
- Heading report dùng tiếng Việt.
- Giữ nguyên tiếng Anh cho tên kỹ thuật chuẩn như file path, class, function, CLI command, env var, model name, package name, schema field.
- Không dùng format nửa Anh nửa Việt.
- Nếu prompt từ ChatGPT có heading tiếng Anh, Codex vẫn trả lời bằng tiếng Việt trừ khi được yêu cầu khác.

Template report chuẩn:

1. Tóm tắt
2. File đã thay đổi
3. Quyết định đã áp dụng
4. Lệnh đã chạy
5. Kết quả test
6. Output/debug đã tạo
7. Rủi ro còn lại
8. Câu hỏi cần quyết định
9. Bước tiếp theo đề xuất

## Known Conflicts

- Tesseract remains in code/docs only as legacy optional.
- `settings.py` and `config.py` still overlap internally, but `settings.py` is canonical for new work.
- Multiple extraction, validation, render, OCR, and Excel writer paths overlap.
- Old app folders exist and need classification before cleanup.

## Suggested Next Step

Ask Project Owner / ChatGPT to approve one Phase 1C/2 slice:

1. Canonical Surya OCR adapter design and real runtime wiring.
2. Debug UI bbox/evidence/QA parity.
3. Canonical extraction package/API selection.
4. Legacy app/archive plan.
5. Local LLM strict JSON/evidence hardening.
