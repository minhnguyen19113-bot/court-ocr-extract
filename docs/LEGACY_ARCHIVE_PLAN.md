# Legacy Archive Plan

Last updated: 2026-07-10

## Nguyên tắc

Phase 1C chỉ lập kế hoạch archive/slimming. Codex không delete, mass-move, hoặc archive tracked files trong phase này.

Mọi action archive/delete sau này cần:

- Project Owner/ChatGPT duyệt nhóm cụ thể.
- Có test trước và sau.
- Có đường rollback rõ.
- Không đụng `data/`, `outputs/`, `logs/`, `work/`, hoặc dữ liệu thật.

## Thứ tự đề xuất

| Giai đoạn | Phạm vi | Action đề xuất | Điều kiện duyệt |
| --- | --- | --- | --- |
| A | App legacy | Removed `app/`, `app_fastapi/`, `app_streamlit/` in Phase 1D. | Restore from Git history if needed. |
| B | Surya adapter trùng | Chọn một adapter canonical, giữ route `--ocr-backend surya`. | `check_ocr_backend --backend surya` và tests Surya vẫn pass. |
| C | Render/preprocess trùng | Chọn render/preprocess API duy nhất. | Debug render/preprocess synthetic tests pass. |
| D | Extraction package trùng | Completed Phase 1F: `extraction_pipeline.py` + `extractors/` canonical; migrate caller và xóa năm duplicate paths. | Synthetic no-network extraction contract tests và architecture guardrail pass. |
| E | Validation/QA trùng | Hợp nhất validation warning/evidence schema. | QA/extraction tests pass. |
| F | Excel/export trùng | Completed Phase 1E: giữ `excel_writer.py`, migrate caller, xóa `excel.py` và `export/excel_writer.py`. | Synthetic Excel contract tests và architecture guardrail pass. |
| G | Cloud/legacy backends | Giữ opt-in adapter hoặc archive vào legacy namespace. | Guardrail xác nhận cloud disabled default. |

## Nhóm không được xóa trong Phase 1C

- `src/court_ocr_extract/ocr_backends/tesseract_ocr.py`: legacy optional còn là backend rõ ràng, không default.
- Cloud adapters: vẫn cần cho opt-in benchmark/so sánh nếu Project Owner yêu cầu.
- VLM path: benchmark path đã được duyệt là candidate, không xóa khi chưa có kết quả so sánh.
- Synthetic tests/fixtures: cần cho contract/control-flow.

## Nhóm có thể archive sau duyệt

| Nhóm | Lý do | Điều kiện trước khi archive |
| --- | --- | --- |
| `app/`, `app_fastapi/`, `app_streamlit/` | Removed in Phase 1D. | Không còn action archive; restore bằng Git history nếu cần. |
| Wrapper Excel trùng | Removed in Phase 1E; không cần wrapper vì mọi caller đã migrate. | Restore bằng Git history trước Phase 1E nếu phát hiện external dependency ngoài repo. |
| Extraction backend/rule trùng | Removed in Phase 1F; typed compatibility adapter nằm trong canonical Local LLM module. | Restore bằng Git history trước Phase 1F nếu phát hiện external dependency ngoài repo. |
| Adapter Surya cũ | `ocr_backends/surya_ocr.py` đang là runtime chính. | Có migration path hoặc shim ổn định. |
| Config compatibility cũ | `settings.py` là canonical. | Không còn import quan trọng từ `config.py`. |

## Phase 1D Result

Phase 1D removed old app folders because audit found no import/runtime dependency from the main CLI package path:

- `app/`
- `app_fastapi/`
- `app_streamlit/`

Also removed stale old-app launch/doc artifacts:

- `scripts/ezycloudx_run_api.sh`
- `scripts/ezycloudx_run_api_windows.ps1`
- `docs/streamlit_vs_fastapi.md`
- `templates/upload.html`

No `legacy/`, `archive/`, `old/`, or `deprecated/` folder was created. Restore path: use Git history before the Phase 1D commit if an old UI is needed for reference.

## Phase 1E Result

Phase 1E consolidated Excel/export without creating an archive folder:

- Canonical: `src/court_ocr_extract/excel_writer.py`.
- Removed: `src/court_ocr_extract/excel.py`.
- Removed: `src/court_ocr_extract/export/excel_writer.py`.
- Compatibility wrapper: none required after repo-wide caller migration.
- Restore path: use Git history before the Phase 1E commit.

## Phase 1F Result

- Canonical orchestrator: `src/court_ocr_extract/extraction_pipeline.py`.
- Canonical backend package: `src/court_ocr_extract/extractors/`.
- Removed: `extraction/base.py`, `extraction/local_llm_extractor.py`, `extraction/rule_support.py`, `extractor.py`, `llm.py`.
- Compatibility wrapper: none; typed adapter được giữ trong canonical module.
- Direct vision/cloud adapters: giữ benchmark/opt-in, không default.
- Restore path: use Git history before the Phase 1F commit.

## Kiểm tra bắt buộc trước archive

```powershell
.\.venv\Scripts\python -B -m compileall src scripts -q
.\.venv\Scripts\python -B -m scripts.check_repo_guardrails
.\.venv\Scripts\python -B -m scripts.check_architecture_guardrails
.\.venv\Scripts\python -B -m pytest -p no:cacheprovider
git diff --check
```
