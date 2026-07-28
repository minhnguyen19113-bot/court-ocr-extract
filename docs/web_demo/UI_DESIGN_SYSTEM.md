# Hệ thống thiết kế giao diện web demo

## 1. Mục tiêu

Giao diện phục vụ người dùng nghiệp vụ không chuyên kỹ thuật. Thiết kế ưu tiên
khả năng đọc tiếng Việt, cấu trúc rõ, cảm giác trang trọng và hành động có thể
đoán trước. Đây là giao diện thử nghiệm, không sử dụng nhận diện chính thức của
Tòa án hoặc cơ quan nhà nước.

## 2. Typography

- Font chính: system stack `"Segoe UI", "Noto Sans", Arial, sans-serif`.
- Không tải font từ CDN, Google Fonts hoặc URL bên ngoài.
- Body: `16px`, line-height `1.56`.
- Menu: `15.5px`, line-height `1.35`.
- H1: `38–44px`, line-height `1.18`, không tracking âm.
- H2 cấp trang/section: `24–28px`; heading trong card: `20px`.
- Heading trong summary card và list: `16px`.
- Eyebrow: `12px`, tracking tối đa `0.06em`.
- Không dùng chữ in hoa kéo dài cho nội dung tiếng Việt.
- Dấu tiếng Việt phải có đủ line-height; không đặt `overflow: hidden` trên vùng
  chứa heading hoặc label.

System stack được chọn vì hiển thị ổn định trên Windows, không tạo request font
khi build/chạy và không phụ thuộc kết nối mạng.

## 3. Màu sắc

| Vai trò | Token | Giá trị |
| --- | --- | --- |
| Navy nền điều hướng | `--navy-950` | `#0b1f33` |
| Navy heading | `--navy-900` | `#132f4c` |
| Navy tương tác | `--navy-800` | `#1e456b` |
| Burgundy hành động chính | `--burgundy-800` | `#6d2836` |
| Gold trạng thái thử nghiệm | `--gold-700` | `#8a681d` |
| Nền trang | `--background` | `#f5f6f7` |
| Nền nội dung | `--surface` | `#ffffff` |
| Focus | `--focus` | `#9b6b00` |

Không dùng gradient, neon, purple/pink startup palette hoặc glass effect. Màu
trạng thái luôn đi cùng text và icon.

## 4. Kích thước và khoảng cách

- Sidebar desktop: `264px`, nằm trong khoảng chấp nhận `250–280px`.
- Top bar: `64px`.
- Content max-width: `1440px`.
- Khoảng cách chính giữa các khối: `25px`.
- Card padding: `20–28px`.
- Action/control tối thiểu: `40–43px`.
- Radius: `4px`, `7px`, tối đa `10px`.
- Shadow: chỉ `0 2px 8px rgb(11 31 51 / 6%)`.

## 5. Component chuẩn

- `AppShell`: sidebar, top bar và `main` dùng chung.
- `Sidebar`: đúng 10 mục nghiệp vụ, active state navy/gold và `aria-current`.
- `TopBar`: một `EnvironmentBadge`, một notification button và
  `UserMenuPlaceholder`.
- `PageHeader`: eyebrow, H1, mô tả và đúng một primary action.
- `SummaryCard`: label, số liệu, status có text/icon và helper.
- `StatusBadge`: text + Lucide icon; không truyền đạt trạng thái chỉ bằng màu.
- `SectionCard`: heading, mô tả và nội dung theo nhịp thống nhất.
- `EmptyState`: trạng thái rỗng, giải thích và bước tiếp theo.
- `PrimaryAction`: link hoặc button; tính năng chưa khả dụng phải disabled.

## 6. Icon

Icon dùng `lucide-react@1.27.0` từ repository
`https://github.com/lucide-icons/lucide.git`, license `ISC`, stroke mặc định
`1.8–2`. Icon trang trí có `aria-hidden=true`; icon-only control bắt buộc có
accessible name. Không tự vẽ SVG riêng, không dùng emoji và không dùng asset
icon từ URL bên ngoài.

## 7. Ngôn ngữ

Nhãn chính dùng ngôn ngữ nghiệp vụ: hồ sơ, xử lý, kiểm tra, phê duyệt, kết quả,
biểu mẫu và nhật ký. Không đưa jargon kỹ thuật vào UI thông thường. Thông tin
kỹ thuật chỉ được đặt trong khu vực quản trị nâng cao khi thật sự cần.

Một trang placeholder phải trả lời:

1. Đây là trang gì?
2. Người dùng có thể làm gì?
3. Tính năng hiện ở trạng thái nào?
4. Bước tiếp theo là gì?

## 8. Accessibility

- Có skip link đến `main`.
- Landmark `nav` và `main` rõ.
- Focus ring `3px` nhìn thấy trên nền sáng/tối.
- Heading theo thứ bậc H1 → H2 → H3.
- Form control luôn có label.
- `aria-current="page"` cho route active.
- Icon trang trí không tạo tên thừa cho screen reader.
- Trạng thái và cảnh báo có text; không chỉ dùng màu.

Visual QA của Project Owner vẫn cần xác nhận contrast thực tế, zoom, reflow và
dấu tiếng Việt trong browser.
