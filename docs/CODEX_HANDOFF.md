# Codex Handoff

Last updated: 2026-07-10

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
9. `docs/REPO_INVENTORY.md`, `docs/IMPORT_GRAPH.md`, `docs/LEGACY_ARCHIVE_PLAN.md`, and `docs/PRODUCTION_TOOLKIT.md` if architecture audit, cleanup/archive, or production readiness is involved
10. `docs/EVALUATION_PLAN.md`, `docs/GOLD_DATASET_GUIDE.md`, `docs/PRIVACY_REDACTION_PLAN.md`, `docs/OBSERVABILITY_PLAN.md`, and `docs/MLOPS_PLAN.md` if evaluation, privacy, observability, or runtime/model governance is involved

## Current State

Phase 1C đã thêm architecture audit + repo slimming plan + production toolkit blueprint. Các artifact mới:

- `scripts/repo_inventory.py`
- `scripts/import_graph.py`
- `scripts/check_architecture_guardrails.py`
- `docs/REPO_INVENTORY.md`
- `docs/IMPORT_GRAPH.md`
- `docs/LEGACY_ARCHIVE_PLAN.md`
- `docs/PRODUCTION_TOOLKIT.md`
- `docs/EVALUATION_PLAN.md`
- `docs/GOLD_DATASET_GUIDE.md`
- `docs/PRIVACY_REDACTION_PLAN.md`
- `docs/OBSERVABILITY_PLAN.md`
- `docs/MLOPS_PLAN.md`

Phase 1C không xóa file, không archive/mass-move tracked code, không chạy dữ liệu thật, không inspect protected artifacts, và không push khi chưa được yêu cầu.

Phase 1D removed old app/UI folders after audit confirmed no main `src/`/CLI import dependency:

- Removed `app/`
- Removed `app_fastapi/`
- Removed `app_streamlit/`
- Removed `docs/streamlit_vs_fastapi.md`
- Removed `scripts/ezycloudx_run_api.sh`
- Removed `scripts/ezycloudx_run_api_windows.ps1`
- Removed `templates/upload.html`
- Removed `streamlit` and `jinja2` from optional `web` dependencies

Restore path: use Git history before the Phase 1D commit if an old UI is needed. Do not recreate `legacy/`, `archive/`, `old/`, or `deprecated/` folders for this code unless Project Owner explicitly asks.

Phase 1E consolidated Excel/export paths:

- Canonical: `src/court_ocr_extract/excel_writer.py`.
- Migrate pipeline, evaluation script, và tests sang canonical import.
- Removed `src/court_ocr_extract/excel.py`.
- Removed `src/court_ocr_extract/export/excel_writer.py`.
- Không tạo compatibility wrapper vì không còn caller trong repo.
- Restore path: use Git history before the Phase 1E commit.
- Workbook schema vẫn là 11 domain headers; 8 audit/trace columns mục tiêu cần phase schema riêng.

Phase 1F consolidated extraction modules:

- Canonical orchestrator: `src/court_ocr_extract/extraction_pipeline.py`.
- Canonical package: `src/court_ocr_extract/extractors/`.
- Canonical Local LLM: `src/court_ocr_extract/extractors/local_llm_extractor.py`.
- Canonical rule helper: `src/court_ocr_extract/extractors/rule_support.py`.
- Removed `extraction/base.py`, `extraction/local_llm_extractor.py`, `extraction/rule_support.py`, root `extractor.py`, và root `llm.py`.
- `extraction/` chỉ còn typed merge/schema/validation/GLiNER helpers, không phải backend owner.
- `TypedLocalLLMExtractor` giữ old typed pipeline behavior trong canonical module; không có wrapper file.
- `scripts.check_extractor` là static config check, không endpoint request.
- Restore path: use Git history before the Phase 1F commit.

TOOLKIT-1 added a privacy-aware evaluation foundation:

- Package: `src/court_ocr_extract/evaluation/`.
- Scripts: `scripts/check_gold_manifest.py`, `scripts/evaluate_gold_manifest.py`.
- Synthetic fixtures: `tests/fixtures/gold_manifest_synthetic.jsonl`, `prediction_manifest_synthetic.jsonl`.
- Report chỉ whitelist aggregate numeric metrics, không chứa raw expected/predicted values.
- `data_private/`, `data/gold/` và manifest ngoài `tests/fixtures/` bị guardrail chặn.
- Gold thật không commit/không đưa vào Codex; Project Owner review và chạy ngoài Codex.
- TOOLKIT-1 chưa nối trực tiếp pipeline output thật và chưa tính OCR CER/WER.

Phase 2A đã triển khai đường chạy Surya OCR ở mức code/contract và thêm artifact để review OCR bằng hình ảnh. README, `.env.example`, Ezycloudx docs, visual QA docs, workflow docs, run scripts, và `settings.py` vẫn trỏ về default Surya target thay vì Tesseract.

Canonical decisions:

- `src/court_ocr_extract/settings.py` is canonical rebuild config.
- `src/court_ocr_extract/config.py` is compatibility/legacy.
- `src/court_ocr_extract/excel_writer.py` là canonical Excel writer duy nhất; không import hai path đã xóa.
- `src/court_ocr_extract/extraction_pipeline.py` và `src/court_ocr_extract/extractors/` là canonical extraction path.
- `src/court_ocr_extract/evaluation/` là canonical manifest/metrics/report toolkit.
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

Preprocess safety notes:

- Auto-deskew `minAreaRect` cũ đã bị thay; canonical preprocess default không rotate.
- `debug-preprocess` default: `--deskew off --red-seal-removal on --preprocess-profile conservative`.
- Red mask/removal chạy trên original color trước grayscale; output có per-page `red_mask.png`, `seal_removed.png`, `final_preprocessed.png` và `metadata.json`.
- `safe` deskew chỉ rotate khi đủ confidence và qua angle/crop/multi-column guard; rotation mở rộng canvas.
- Blank guard fallback về original/previous safe stage và ghi warnings rõ.
- Không có real PDF/OCR run trong task; Project Owner phải review bản `off` trên Ezycloudx trước khi tiếp tục OCR.

Red seal/text enhancement v2 notes:

- Default CLI: `--red-removal-mode neutralize --text-enhance light`; deskew vẫn `off`.
- Detector dùng HSV + Lab + RGB; artifacts thêm `black_text_protection_mask.png` và `text_enhanced.png`.
- Modes: `neutralize` bảo thủ, `inpaint` làm sạch residual hai lượt, `white_fill` chỉ thử nghiệm.
- Protection mask giữ nét tối; overlap đáng kể ghi `red_mask_overlaps_dark_text`.
- Text enhancement chạy sau red removal; guard fallback khi dark pixels/foreground bùng nổ hoặc entropy collapse.
- Project Owner cần so sánh ba run v2 trong runbook; Codex chưa đọc/chạy real PDF/output.

Repo cleanup notes:

- Generated cache local đã được dọn khỏi workspace.
- Tracked legacy/duplicate modules chưa bị xóa; chúng vẫn cần canonical owner decision trước khi archive/delete.
- Không inspect hoặc cleanup protected real-data folders trong Codex.

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
- Validation, render, và OCR paths vẫn overlap; Excel/extraction backend overlap đã được xử lý trong Phase 1E/1F.
- Old app folders were removed in Phase 1D; do not reintroduce old app run instructions in README/docs/scripts.

## Suggested Next Step

Ask Project Owner / ChatGPT to approve one next slice:

1. Project Owner so sánh `neutralize+light`, `inpaint+light`, `inpaint+medium` theo runbook.
2. Chọn mode giảm red residual nhưng giữ được black-text protection và dấu tiếng Việt.
3. Chỉ sau preprocess gate mới tiếp tục Surya visual QA/OCR.
