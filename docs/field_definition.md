# Field Definition

Excel output có 11 cột:

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

`GHI CHÚ` dùng cho lý do thiếu dữ liệu, confidence thấp, conflict giữa extractor, JSON lỗi hoặc thiếu marker.

Các cột sau bị loại bỏ:

- `HỌ TÊN NGƯỜI NHẬP`
- `EMAIL NGƯỜI NHẬP`
- `SỐ ĐIỆN THOẠI`
