# Nguyên tắc tham chiếu giao diện pháp lý và dịch vụ công

## 1. Phạm vi tham chiếu

Phase 0.8 chỉ tham chiếu các nguyên tắc phổ quát của giao diện pháp lý/dịch vụ
công: trang trọng, minh bạch, dễ đọc, ít trang trí và đặt quy trình trước số
liệu. Không sao chép website, logo, quốc huy, huy hiệu, con dấu, biểu tượng hay
đồ họa nhận diện của cơ quan cụ thể.

## 2. Nguyên tắc áp dụng

1. **Thẩm quyền qua cấu trúc, không qua biểu tượng.** Cảm giác đáng tin đến từ
   heading rõ, khoảng trắng, màu navy/burgundy tiết chế và trạng thái minh bạch.
2. **Nghiệp vụ trước kỹ thuật.** Người dùng thấy “Xử lý hồ sơ”, “Kiểm tra dữ
   liệu”, “Phê duyệt”; chi tiết triển khai không xuất hiện trong luồng chính.
3. **Một trang, một hành động chính.** Hành động chưa khả dụng vẫn được trình bày
   rõ nhưng disabled, kèm lý do và bước tiếp theo.
4. **Trạng thái không mơ hồ.** Nhãn, icon và giải thích đi cùng nhau; “Đã phê
   duyệt” khác “Đã công bố”.
5. **Dữ liệu minh họa phải được nói rõ một lần.** Không lặp nhãn kỹ thuật trên
   từng card và không tạo cảm giác số liệu thật.
6. **Mật độ vừa phải.** Dashboard chỉ giữ bốn số liệu chính và tối đa hai vùng
   phụ.
7. **Khả năng đọc tiếng Việt là tiêu chí đầu tiên.** Font, line-height và
   letter-spacing phải bảo toàn dấu; không dùng typography quảng cáo.
8. **Tương tác đoán trước được.** Điều hướng giữ vị trí ổn định, active state rõ,
   control có label và focus nhìn thấy.

## 3. Những gì không sử dụng

- Official emblem/logo, quốc huy, huy hiệu, con dấu hoặc hình Tòa án thật.
- Ảnh người, hồ sơ, giấy tờ hoặc phòng xử án.
- Remote image/font URL.
- Gradient, glassmorphism, neon, purple/pink startup palette.
- Sales dashboard, biểu đồ trang trí hoặc số liệu gây hiểu nhầm.
- Wording tạo cảm giác authentication, phân quyền hoặc capability thật đã hoàn
  thành.

## 4. Hệ quả triển khai

Brand mark trong sidebar là Lucide `Scale` trừu tượng, không phải logo chính
thức. Giao diện dùng system font stack và Lucide package exact. Mọi đánh giá về
độ trang trọng trong browser thuộc visual QA của Project Owner, không được suy
ra chỉ từ static test hoặc build.
