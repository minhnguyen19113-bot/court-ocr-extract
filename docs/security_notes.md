# Security Notes

Dữ liệu bản án có thể chứa thông tin cá nhân. Thiết kế mặc định của dự án là local-first và không phát tán dữ liệu ra dịch vụ cloud.

## Mặc định an toàn

- `ENABLE_CLOUD_LLM_EXTRACTION=false`.
- `FORCE_FULL_OCR=false`.
- `DEBUG_SENSITIVE=false`.
- `PERSIST_OCR_TEXT_ARTIFACTS=false`.
- `PERSIST_SENSITIVE_TEXT_IN_JSON=false`.
- Không log full OCR text mặc định.
- Không commit `data/`, `outputs/`, `.env`, `logs/`, `cache/`, `models/`.

## Khi dùng Ezycloudx

Ezycloudx vẫn là hạ tầng thuê từ bên ngoài. Chỉ dùng instance như GPU runtime tạm thời:

- Không lưu dữ liệu dài hạn trên remote.
- Không upload output sang dịch vụ thứ ba.
- Ưu tiên thao tác qua RDP và mở UI/API trong chính VM.
- Nếu expose API ra ngoài VM thì dùng endpoint private có token.
- Remote chỉ xử lý file trong workspace tạm thời hoặc temp dir worker.
- Chạy `/cleanup` hoặc `python -m scripts.cleanup_remote_worker` sau batch.
- Nếu chạy toàn bộ pipeline trên Ezycloudx, tải Excel/JSON về local rồi xóa `data/` artifacts và `outputs/` nếu không cần giữ.

## Logging

Log mặc định chỉ nên chứa:

- `file_id`
- số trang
- số trang OCR
- thời gian xử lý
- trạng thái
- lỗi kỹ thuật

Chỉ bật `DEBUG_SENSITIVE=true` khi debug cục bộ, có kiểm soát, và không chia sẻ log.

## OCR artifacts

OCR raw JSON, ảnh render, ảnh processed, bbox debug và Excel output đều có thể là derived sensitive artifacts. Chúng nằm trong `data/` hoặc `outputs/` và đã được `.gitignore`.

Theo mặc định, artifact JSON/CLI/API payload không nhúng full OCR buffer:

- `text_before_marker` được đặt `null`.
- `corrected_text` được đặt `null`.
- `metadata.ocr_pages` được bỏ khỏi JSON artifact và đánh dấu `ocr_pages_redacted=true`.

Bật `PERSIST_OCR_TEXT_ARTIFACTS=true` chỉ khi cần ghi file `.txt` để debug cục bộ. Bật `PERSIST_SENSITIVE_TEXT_IN_JSON=true` hoặc `DEBUG_SENSITIVE=true` chỉ trong phiên debug có kiểm soát, sau đó cleanup dữ liệu.

## Remote fallback

Remote GPU worker có fallback cấu hình được:

- `GPU_WORKER_FALLBACK=true` cho phép thử OCR local nếu worker tạm không sẵn sàng.
- `GPU_WORKER_FALLBACK_TO_MOCK=false` mặc định để tránh vô tình tạo kết quả mock trên dữ liệu thật.

Chỉ bật fallback sang mock khi kiểm thử synthetic.
