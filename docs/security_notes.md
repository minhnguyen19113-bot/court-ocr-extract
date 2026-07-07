# Security Notes

Dữ liệu bản án có thể chứa thông tin cá nhân. Thiết kế mặc định của dự án là local-first và không phát tán dữ liệu ra dịch vụ cloud nếu chưa bật opt-in rõ ràng.

## Mặc Định An Toàn

- `ENABLE_CLOUD_OCR=false`.
- `ENABLE_CLOUD_EXTRACTION=false`.
- `FORCE_FULL_OCR=false`.
- `SAVE_DEBUG_JSON=false`.
- Không log full OCR text mặc định.
- Không commit `data/`, `outputs/`, `.env`, `logs/`, `cache/`, `models/`.

## Real-Data Validation

Không dùng dữ liệu giả để đánh giá chất lượng OCR/extraction. Chất lượng phải được người dùng kiểm tra trên real-data pilot PDF thật qua visual QA, extraction preview, Excel và QA summary.

Codex không tự mở, đọc, OCR, parse hoặc quote nội dung PDF thật hay derived artifact thật. Người dùng chạy workflow dữ liệu thật trực tiếp trên VM/máy nội bộ.

## Ezycloudx

Ezycloudx vẫn là hạ tầng thuê ngoài. Chỉ dùng instance như runtime tạm thời:

- Không lưu dữ liệu dài hạn trên remote.
- Không upload output sang dịch vụ thứ ba.
- Nếu expose transfer server thì dùng host `127.0.0.1` và Cloudflare tunnel tạm thời có token.
- Sau batch, tải Excel/debug zip cần thiết rồi dọn `data/` và `outputs/` nếu không cần giữ.

## Logging

Log mặc định chỉ nên chứa:

- `case_id`
- số trang
- số trang OCR
- thời gian xử lý
- trạng thái
- lỗi kỹ thuật

Không in họ tên, địa chỉ, CCCD/CMND, full OCR text hoặc tên file PDF thật.

## Runtime Artifacts

OCR cache, ảnh render, ảnh processed, bbox debug, extraction preview và Excel output đều có thể là derived sensitive artifacts. Chúng nằm trong `data/` hoặc `outputs/` và đã được `.gitignore`.

Synthetic smoke artifacts under `outputs/debug_visual/synthetic_smoke/`, `outputs/extraction_draft/synthetic_smoke/`, `outputs/excel/synthetic_smoke.xlsx`, and `outputs/qa/synthetic_smoke_report.json` are safe to inspect because they are generated from non-real contract fixtures by `python -m scripts.smoke_synthetic_debug`.

## Fallback

Không fallback âm thầm giữa backend/extractor. Fallback OCR chỉ chạy khi người dùng truyền rõ `--fallback-ocr-backend`.

Không bật mock/fake fallback trong workflow dữ liệu thật.
