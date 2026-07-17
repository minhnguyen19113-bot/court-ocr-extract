# Hướng dẫn annotation

Tạo annotation bằng dữ liệu giả lập hoặc dữ liệu thật do người dùng tự xử lý ngoài Codex.

Mỗi dòng final tương ứng một người tham gia tố tụng và dùng đúng 11 cột:

- `LOẠI ÁN`
- `SỐ THỤ LÝ`
- `NGÀY THỤ LÝ (DD/MM/YYYY)`
- `QUAN HỆ PHÁP LUẬT`
- `TƯ CÁCH TỐ TỤNG`
- `HỌ TÊN ĐƯƠNG SỰ`
- `NĂM SINH`
- `CCCD`
- `ĐỊA CHỈ`
- `HỌ TÊN CHỦ TỌA`
- `GHI CHÚ`

`source_file` và `row_index` chỉ là metadata của annotation/debug, không thuộc
schema `FINAL_EXCEL`.

Không đưa dữ liệu cá nhân thật vào fixture test của repo.
