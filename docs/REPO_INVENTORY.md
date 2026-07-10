# Repo Inventory

Last updated: 2026-07-10

## Mục tiêu

Tài liệu này ghi lại inventory an toàn cho Phase 1C. Codex chỉ kiểm tra code, config, docs, prompts, scripts, tests và contract fixtures. Codex không đọc `data/`, `outputs/`, `logs/`, `work/`, PDF thật, ảnh thật, OCR thật, Excel thật, hoặc model output thật.

Script nguồn: `python -m scripts.repo_inventory`.

## Phạm vi scan an toàn

- Root docs/config: `AGENTS.md`, `README.md`, `pyproject.toml`, `.env.example`, `docs/`, `config/`, `prompts/`.
- Code/tooling: `src/`, `scripts/`, `tests/`.
- Bỏ qua: `.git/`, `.venv/`, cache folders, `data/`, `outputs/`, `logs/`, `work/`, `models/`.

## Snapshot Phase 1C

- Safe files scanned: 241.
- Code files: 162.
- Docs/prompt files: 48.
- Config files: 9.
- Root keep files: 5.

## Snapshot Phase 1D

- Safe files scanned: 229.
- Code files: 160.
- Docs/prompt files: 47.
- Config files: 9.
- Root keep files: 5.
- Optional app dirs: none.

## Snapshot Phase 1E

- Safe files scanned: 228.
- Code files: 159.
- Docs/prompt files: 47.
- Config files: 9.
- Root keep files: 5.
- Excel writer duplicate group: none.

## Nhóm chính đang giữ

| Nhóm | Trạng thái | Ghi chú |
| --- | --- | --- |
| `src/court_ocr_extract/settings.py` | canonical | Config rebuild chính. |
| `src/court_ocr_extract/ocr_backends/surya_ocr.py` | main candidate | Surya runtime path hiện tại. |
| `src/court_ocr_extract/ocr_cache.py` | main candidate | Contract OCR cache. |
| `src/court_ocr_extract/excel_writer.py` | canonical | Excel writer duy nhất sau Phase 1E; chứa draft-record và typed-result APIs. |
| `src/court_ocr_extract/local_llm/` | main candidate | Local LLM client/parser/prompt builder. |
| `src/court_ocr_extract/visual_debug.py`, `review_html.py` | main candidate | Visual QA/debug UI. |
| `scripts/project_snapshot.py`, `check_repo_guardrails.py` | guardrail tooling | Memory/safety checks. |

## Nhóm chồng lấn cần quyết định

| Nhóm | File hiện có | Quyết định cần duyệt |
| --- | --- | --- |
| PDF render | `src/court_ocr_extract/pdf_render.py`, `src/court_ocr_extract/pdf/render.py` | Chọn API render canonical. |
| Preprocess | `preprocess.py`, `image_preprocess.py`, `image_processing/preprocess.py` | Chọn một entrypoint preprocess. |
| Surya adapter | `ocr_backends/surya_ocr.py`, `ocr_surya.py`, `ocr/surya_adapter.py` | Giữ `ocr_backends/surya_ocr.py` làm runtime chính hay chuyển vào package `ocr/`. |
| Local LLM extractor | `extraction/local_llm_extractor.py`, `extractors/local_llm_extractor.py` | Chọn package extraction canonical. |
| Validation | `validation.py`, `validator.py`, `extraction/validators.py` | Hợp nhất warning/evidence rules. |

## Nhóm legacy/optional

- `src/court_ocr_extract/ocr_backends/tesseract_ocr.py`: legacy optional, không main/default.
- Cloud OCR adapters: `google_vision_ocr.py`, `google_document_ai_ocr.py`, `openai_vision_ocr.py`, `gemini_document_ocr.py`; chỉ opt-in benchmark.
- Cloud/direct extractors: `openai_extractor.py`, `gemini_extractor.py`, `direct_vision_extractor.py`; không bật mặc định.
- `app/`, `app_fastapi/`, `app_streamlit/`: removed in Phase 1D after audit found no main `src/`/CLI import dependency. Restore path: use Git history before the Phase 1D commit if needed.

## Nhóm đã xử lý trong Phase 1E

| Nhóm | Canonical | Path đã xóa | Restore path |
| --- | --- | --- | --- |
| Excel writer | `src/court_ocr_extract/excel_writer.py` | `src/court_ocr_extract/excel.py`, `src/court_ocr_extract/export/excel_writer.py` | Git history trước Phase 1E commit. |

## Kết luận hiện tại

Phase 1E đã xử lý riêng nhóm Excel/export sau approval và audit caller. Repo vẫn chưa đủ điều kiện xóa tracked code hàng loạt ở các nhóm Surya, extraction, validation, render/preprocess; các nhóm này tiếp tục cần approval và test riêng.
