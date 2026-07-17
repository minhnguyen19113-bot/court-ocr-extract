# Field Definition

Sheet đầu `FINAL_EXCEL` là output chính và có đúng 11 cột:

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

Mỗi người tham gia tố tụng là một dòng. Các thông tin chung của vụ án được lặp lại trên từng dòng.

`GHI CHÚ` dùng cho lý do thiếu dữ liệu, confidence thấp, conflict giữa extractor, validator hoặc thiếu marker. Không đưa JSON blob vào cột này; evidence/trace đầy đủ nằm trong debug sheets.

Các cột sau bị loại bỏ:

- `HỌ TÊN NGƯỜI NHẬP`
- `EMAIL NGƯỜI NHẬP`
- `SỐ ĐIỆN THOẠI`
