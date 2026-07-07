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

Phase 2A đã triển khai đường chạy Surya OCR ở mức code/contract và thêm artifact để review OCR bằng hình ảnh. README, `.env.example`, Ezycloudx docs, visual QA docs, workflow docs, run scripts, và `settings.py` vẫn trỏ về default Surya target thay vì Tesseract.

Canonical decisions:

- `src/court_ocr_extract/settings.py` is canonical rebuild config.
- `src/court_ocr_extract/config.py` is compatibility/legacy.
- `src/court_ocr_extract/excel_writer.py` is canonical Excel writer.
- Surya OCR + local LLM is the main candidate.
- Local VLM is the benchmark path.

Phase 2A đã có wiring Surya OCR ở mức code/contract, nhưng chất lượng OCR thật chưa được validate trên PDF thật trong Codex.

Phase 2A notes:

- `src/court_ocr_extract/ocr_backends/surya_ocr.py` không còn placeholder `runtime wiring is incomplete`.
- `ocr_pdf_prefix()` đã implement flow `pdf_path` -> `render_pdf_pages()` -> Surya OCR trên rendered images -> normalize `OCRResult`.
- Adapter hỗ trợ API `surya-ocr 0.20.0` bằng `RecognitionPredictor(..., full_page=True)`.
- Nếu API Surya cài đặt không được hỗ trợ, adapter raise lỗi rõ với prefix `Surya package is installed but this adapter does not support the installed API. Detected ...`.
- `--ocr-backend surya` route qua Surya backend.
- `debug-ocr-review` có thể dùng wiring `surya`, nhưng Codex không được chạy command này trên PDF thật.
- Surya artifact theo page được ghi dưới `ocr_surya/` khi bật debug visual.
- Synthetic tests chỉ chứng minh schema/control-flow, không chứng minh chất lượng OCR thật.
- Nếu thiếu Surya, cài bằng `pip install -e ".[ocr]"` hoặc `pip install surya-ocr`.

Full-document debug review notes:

- `debug-render`, `debug-preprocess`, và `debug-red-seal` mặc định chạy toàn bộ trang nếu không truyền `--pages`.
- Muốn giới hạn trang review thì truyền rõ `--pages 1-3` hoặc range tương tự.
- `debug-ocr-review --full-document` truyền `max_pages=None` và `stop_marker=""` vào backend, nên không dừng/truncate tại marker `NỘI DUNG VỤ ÁN`.
- `ocr --full-document` cũng truyền `max_pages=None` và `stop_marker=""`, chỉ tạo OCR cache/debug visual, không chạy extraction/LLM/Excel.
- Pilot 1 PDF nên dùng folder `data\raw_pdfs\pilot_one` với `--limit 1` và `--review-sample-size 1`.

## Important Warnings

- Do not inspect real data directories or outputs.
- Do not run real PDF workflows inside Codex.
- Do not call cloud APIs by default.
- Do not use synthetic smoke to judge real quality.
- Do not clean/delete/archive files until a later cleanup scope is approved.

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

- Tesseract remains in code/docs only as legacy optional; Surya backend must not fallback to Tesseract.
- `settings.py` and `config.py` still overlap internally, but `settings.py` is canonical for new work.
- Multiple extraction, validation, render, OCR, and Excel writer paths overlap.
- Old app folders exist and need classification before cleanup.

## Suggested Next Step

Ask Project Owner / ChatGPT to approve one Phase 1C/2 slice:

1. Ezycloudx Surya package/model check and possible `surya-ocr` version pin.
2. Visual QA improvements after real Surya bbox/text review.
3. Dedicated `ocr-surya-review` command if needed.
4. Canonical extraction package/API selection.
5. Local LLM strict JSON/evidence hardening.
