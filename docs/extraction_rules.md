# Rule Support

Rule/regex không phải extractor chính.

Rule chỉ dùng cho:

- Tìm marker section `NỘI DUNG VỤ ÁN`.
- Chuẩn hóa Unicode và lỗi OCR phổ biến.
- Bắt anchor đơn giản như số thụ lý, ngày, chủ tọa để hỗ trợ validation.
- Tạo warning và bằng chứng hỗ trợ sau khi extractor chính đã chạy.

Không dùng rule làm fallback âm thầm khi local/cloud extractor lỗi.

Không dùng dữ liệu giả để đánh giá chất lượng rule. Khi gặp mẫu mới, cập nhật rule dựa trên pattern đã được người dùng xác nhận từ real-data pilot PDF thật. Unit test chỉ kiểm tra contract/schema/control-flow và không thay thế visual QA trên PDF thật.
