# Bảo mật dữ liệu bản án

- Không commit PDF thật, OCR raw, ảnh render, Excel hoặc JSON kết quả.
- Không chỉnh sửa PDF gốc. Pipeline chỉ copy bản gốc vào `data/raw_pdfs/` và tạo ảnh phụ cho OCR.
- Ảnh đã giảm dấu mộc đỏ chỉ dùng để OCR, không dùng làm bản pháp lý.
- LLM cloud bị tắt mặc định bằng `ENABLE_LLM_CORRECTION=false` và `ENABLE_LLM_EXTRACTION=false`.
- Nếu bật LLM, cần ẩn danh hóa dữ liệu cá nhân và có chấp thuận bảo mật trước khi gửi ra dịch vụ bên ngoài.
