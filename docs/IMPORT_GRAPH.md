# Import Graph

Last updated: 2026-07-10

## Mục tiêu

`scripts/import_graph.py` tạo bản đồ import Python an toàn cho `src/`, `scripts/`, và `tests/` bằng `ast`. Script không mở dữ liệu thật và không chạy pipeline.

## Cách chạy

```powershell
.\.venv\Scripts\python -B -m scripts.import_graph
.\.venv\Scripts\python -B -m scripts.import_graph --json
```

## Ý nghĩa output

- `Python modules scanned`: số module Python được parse.
- `Internal import edges`: số quan hệ import nội bộ giữa các module trong repo.
- `Unimported src modules`: module trong `src/court_ocr_extract/` chưa được module khác import trực tiếp.
- `Parse errors`: lỗi syntax nếu có.

## Snapshot Phase 1C

Lần chạy ban đầu sau khi thêm script Phase 1C:

- Python modules scanned: 149.
- Internal import edges: 271.
- Parse errors: 0.
- Unimported src modules: 9.

## Snapshot Phase 1D

Sau khi xóa old app folders, import graph của `src/`, `scripts/`, và `tests/` vẫn pass:

- Python modules scanned: 149.
- Internal import edges: 271.
- Parse errors: 0.
- Unimported src modules: 9.

Không có module `src/court_ocr_extract` import `app/`, `app_fastapi/`, hoặc `app_streamlit/`.

## Snapshot Phase 1E

Sau khi migrate caller và xóa hai duplicate Excel writer paths:

- Python modules scanned: 148.
- Internal import edges: 271.
- Parse errors: 0.
- Unimported src modules: 9.
- Không còn import `court_ocr_extract.excel` hoặc `court_ocr_extract.export.excel_writer` trong `src/`, `scripts/`, hoặc `tests/`.
- Pipeline, evaluation script, và tests dùng `court_ocr_extract.excel_writer`.

Các module low-fan-in/unimported hiện là tín hiệu audit, chưa phải bằng chứng để xóa:

- `court_ocr_extract.export.json_writer`
- `court_ocr_extract.extraction.base`
- `court_ocr_extract.llm`
- `court_ocr_extract.logging_config`
- `court_ocr_extract.models.local_model_loader`
- `court_ocr_extract.models.vllm_server`
- `court_ocr_extract.ocr.schemas`
- `court_ocr_extract.preprocess`
- `court_ocr_extract.remote_worker.server`

## Quy tắc diễn giải

- Module không được import trực tiếp vẫn có thể là CLI entrypoint, runtime plugin, legacy compatibility, hoặc code dự phòng.
- Không dùng import graph để xóa file trực tiếp.
- Dùng import graph để chọn nhóm cần reviewer duyệt trong `docs/LEGACY_ARCHIVE_PLAN.md`.
