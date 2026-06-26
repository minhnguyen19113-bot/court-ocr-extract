# Rule support

Rule/regex không phải extractor chính trong hướng mới.

Các rule chỉ dùng cho:

- Tìm marker section `NỘI DUNG VỤ ÁN`.
- Chuẩn hóa Unicode và lỗi OCR phổ biến.
- Bắt anchor đơn giản như số thụ lý, ngày, chủ tọa để hỗ trợ kiểm tra.
- Làm fallback kỹ thuật trong mock mode hoặc khi local LLM chưa sẵn sàng.

Không được hard-code theo một file PDF cụ thể. Khi gặp mẫu mới, thêm fixture synthetic và unit test trước khi mở rộng rule.
