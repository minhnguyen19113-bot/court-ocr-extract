# Streamlit vs FastAPI

Core pipeline nằm trong `src/court_ocr_extract/` và không phụ thuộc UI.

## FastAPI

Dùng cho backend triển khai thật:

- upload PDF
- xử lý PDF
- lấy job result
- tải JSON/Excel
- sau này có thể gắn frontend riêng

Chạy:

```bash
uvicorn app_fastapi.main:app --reload
```

## Streamlit

Dùng demo nhanh:

- upload PDF
- chọn local-only hoặc remote GPU worker
- chọn max pages trước marker
- xem OCR text trước marker
- xem JSON extraction
- xem preview bảng
- tải Excel/JSON

Chạy:

```bash
streamlit run app_streamlit/main.py
```
