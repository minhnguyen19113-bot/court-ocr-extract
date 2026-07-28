# Checklist visual QA giao diện Phase 0.8

## 1. Boundary

Project Owner trực tiếp chạy database, backend, frontend và browser theo
`OPERATIONS_RUNBOOK.md`. Dùng dữ liệu minh họa tối thiểu; không mở hồ sơ, PDF,
ảnh hoặc output thật. Codex không chạy visual QA và không xác nhận chất lượng
render thay Project Owner.

## 2. Viewport cần kiểm tra

- [ ] Desktop lớn: `1440 × 900`.
- [ ] Desktop phổ biến: `1280 × 800`.
- [ ] Tablet ngang: `1024 × 768`.
- [ ] Tablet/mobile chuyển layout: `768 × 1024`.
- [ ] Mobile hẹp: `390 × 844`.
- [ ] Zoom browser `200%` ở viewport desktop.

Tại mỗi viewport, kiểm tra:

- [ ] Không có horizontal overflow ngoài bảng có chủ đích.
- [ ] Sidebar/navigation dùng được; active item rõ.
- [ ] Top bar không che hoặc cắt user block/notification.
- [ ] H1, mô tả và primary action không chồng nhau.
- [ ] Dấu tiếng Việt không bị cắt trên heading, menu, button, badge.
- [ ] Focus ring nhìn thấy khi dùng phím Tab.

## 3. Screenshot bắt buộc

Chụp bằng browser do Project Owner điều khiển, không chứa dữ liệu thật:

- [ ] `/dashboard` tại `1440 × 900`.
- [ ] `/dashboard` tại `1024 × 768`.
- [ ] `/dashboard` tại `390 × 844`.
- [ ] `/intake` tại `1440 × 900`.
- [ ] `/jobs` và `/jobs/synthetic-job`.
- [ ] `/review` và `/review/synthetic-review`.
- [ ] `/publishing`.
- [ ] `/exports`.
- [ ] `/forms` và `/forms/synthetic-form`.
- [ ] `/audit`.
- [ ] `/admin`.
- [ ] `/help`.
- [ ] Một screenshot keyboard focus trên navigation.
- [ ] Một screenshot primary action disabled.

## 4. Typography tiếng Việt

- [ ] Kiểm chuỗi: “Tiếp nhận hồ sơ”, “Kiểm tra dữ liệu”, “Đã phê duyệt”.
- [ ] Kiểm chuỗi: “Kết quả và xuất file”, “Hướng dẫn sử dụng”.
- [ ] Dấu `ă â ê ô ơ ư đ` và dấu thanh hiển thị đủ.
- [ ] Không có fallback font bất thường giữa ký tự có dấu và không dấu.
- [ ] H1 không quá lớn; body không nhỏ hơn mức dễ đọc.
- [ ] Eyebrow không bị giãn chữ quá mức.

## 5. Navigation và shell

- [ ] Sidebar có đúng 10 mục theo thứ tự đã duyệt.
- [ ] Không có mục “Kiểm tra OCR”.
- [ ] Active state là navy/gold, không tím/hồng.
- [ ] Brand hiển thị “Nền tảng dữ liệu Tòa án”.
- [ ] Top bar chỉ có một badge “Bản thử nghiệm”.
- [ ] Không có “Môi trường local · Phase 0”.
- [ ] Không có “Vai trò: Chưa cấu hình”.
- [ ] Notification button có focus và tooltip/accessibility name phù hợp.

## 6. Dashboard

- [ ] Có đúng bốn summary card.
- [ ] Thứ tự: hồ sơ mới, đang xử lý, chờ kiểm tra, đã phê duyệt.
- [ ] “Dữ liệu minh họa” chỉ xuất hiện một lần.
- [ ] Có đúng hai vùng phụ: công việc và lối tắt.
- [ ] Không có card “Chờ công bố” hoặc “Biểu mẫu đã sinh”.
- [ ] Không có jargon kỹ thuật trong nội dung chính.

## 7. Placeholder page

Trên mỗi trang kiểm tra:

- [ ] H1 và mô tả trả lời trang này dùng để làm gì.
- [ ] Có đúng một primary action.
- [ ] Action chưa khả dụng ở trạng thái disabled.
- [ ] Lý do chưa khả dụng được viết bằng ngôn ngữ phổ thông.
- [ ] Empty state nói rõ bước tiếp theo.
- [ ] Không tạo cảm giác đã xử lý/lưu/phê duyệt thật.

## 8. Accessibility thủ công

- [ ] Tab đầu tiên cho phép dùng skip link.
- [ ] `aria-current` tương ứng route hiện tại.
- [ ] Icon trang trí không được screen reader đọc thành ký tự rác.
- [ ] Notification icon có tên “Xem thông báo”.
- [ ] Status có text và icon, vẫn hiểu khi bỏ màu.
- [ ] Label click/focus đúng control.
- [ ] Heading order không bỏ cấp.
- [ ] Contrast được kiểm bằng công cụ browser; ghi lại mọi điểm chưa đạt.

## 9. Cách báo lỗi

Gửi:

- route;
- viewport và zoom;
- screenshot không chứa dữ liệu thật;
- bước tái hiện;
- expected/actual ngắn;
- mức độ ảnh hưởng.

Không gửi `.env`, credential, response nghiệp vụ, tên người, địa chỉ, CCCD/CMND,
PDF, ảnh hồ sơ hoặc đường dẫn artifact thật.
