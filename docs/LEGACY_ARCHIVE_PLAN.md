# Legacy Archive Plan

Last updated: 2026-07-09

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
| D | Extraction package trùng | Chọn `extraction/` hoặc `extractors/` làm canonical. | Local LLM contract tests pass. |
| E | Validation/QA trùng | Hợp nhất validation warning/evidence schema. | QA/extraction tests pass. |
| F | Excel/export trùng | Giữ `excel_writer.py`, archive wrapper trùng nếu không còn caller. | Excel mapping/writer tests pass. |
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
| Wrapper Excel trùng | `excel_writer.py` đã là canonical. | Import graph không còn caller runtime. |
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

## Kiểm tra bắt buộc trước archive

```powershell
.\.venv\Scripts\python -B -m compileall src scripts -q
.\.venv\Scripts\python -B -m scripts.check_repo_guardrails
.\.venv\Scripts\python -B -m scripts.check_architecture_guardrails
.\.venv\Scripts\python -B -m pytest -p no:cacheprovider
git diff --check
```
