# Kiến trúc thông tin giao diện

## 1. Một website, hai phân hệ

Application shell chứa đồng thời:

- tiếp nhận, xử lý, kiểm tra, phê duyệt và xuất dữ liệu;
- chuẩn bị biểu mẫu.

Biểu mẫu không phải ứng dụng hoặc deployment riêng. Hai phân hệ dùng chung
navigation, identity placeholder, capability, version, audit context và status
vocabulary.

## 2. Application shell

### Sidebar

Sidebar desktop rộng `264px`, có đúng 10 mục:

| Thứ tự | Nhãn | Route | Mục đích bản thử nghiệm |
| ---: | --- | --- | --- |
| 1 | Tổng quan | `/dashboard` | Bốn chỉ số chính, công việc và lối tắt |
| 2 | Tiếp nhận hồ sơ | `/intake` | Placeholder tiếp nhận, chưa nhận tệp thật |
| 3 | Xử lý hồ sơ | `/jobs` | Danh sách và tiến độ hồ sơ |
| 4 | Kiểm tra dữ liệu | `/review` | Đối chiếu trường dữ liệu |
| 5 | Phê duyệt | `/publishing` | Điều kiện và hàng đợi phê duyệt |
| 6 | Kết quả và xuất file | `/exports` | Kết quả và định dạng Excel |
| 7 | Biểu mẫu | `/forms` | Danh mục và tình trạng chuẩn bị biểu mẫu |
| 8 | Nhật ký | `/audit` | Hoạt động nghiệp vụ an toàn |
| 9 | Quản trị hệ thống | `/admin` | Cấu hình và thông tin nâng cao |
| 10 | Hướng dẫn sử dụng | `/help` | Quy trình bằng ngôn ngữ phổ thông |

“Kiểm tra OCR” không còn là mục navigation chính. Route chi tiết `/jobs/[jobId]`
vẫn giữ khả năng hiển thị tiến độ nội bộ trong tương lai, nhưng UI thông thường
không dùng jargon kỹ thuật.

Brand copy:

- `Nền tảng dữ liệu Tòa án`;
- `Hồ sơ · Dữ liệu · Biểu mẫu`.

Icon `Scale` là dấu hiệu trừu tượng từ Lucide, không phải logo hoặc nhận diện
chính thức.

### Top bar

Top bar cao `64px` và chỉ gồm:

- một badge nhỏ `Bản thử nghiệm`;
- notification button có accessible name;
- `Người dùng thử nghiệm`.

Không hiển thị environment local, tên phase, “Chưa chính thức” lặp lại hoặc vai
trò chưa cấu hình.

## 3. Dashboard

Dashboard có đúng bốn summary card:

1. Hồ sơ mới tiếp nhận.
2. Đang xử lý.
3. Chờ kiểm tra.
4. Đã phê duyệt.

Chỉ có một note `Dữ liệu minh họa`. Hai section phụ:

- `Công việc cần xử lý`;
- `Lối tắt`.

Primary action là `Tiếp nhận hồ sơ`.

## 4. Route map

| Route | Trạng thái/empty state |
| --- | --- |
| `/dashboard` | Bốn số liệu minh họa, công việc, lối tắt |
| `/intake` | Chưa nhận tệp; action disabled |
| `/jobs` | Chưa có hồ sơ phù hợp; action disabled |
| `/jobs/[jobId]` | Tiến độ ba bước và mã tham chiếu |
| `/review` | Danh mục trường từ contract dùng chung |
| `/review/[reviewId]` | Ghi chú kiểm tra và mã tham chiếu |
| `/publishing` | Điều kiện phê duyệt; action disabled |
| `/exports` | Chỉ giới thiệu Excel; action disabled |
| `/forms` | Định dạng bằng wording phổ thông; action disabled |
| `/forms/[formId]` | Nguồn thông tin và thiết lập đầu ra |
| `/audit` | Lọc hoạt động; empty state có bước tiếp theo |
| `/admin` | Cấu hình read-only và details nâng cao |
| `/help` | Năm bước sử dụng và link tiếp nhận |

Mỗi route có H1, mô tả, đúng một primary action, trạng thái hiện tại và bước
tiếp theo. Chức năng chưa khả dụng phải disabled.

## 5. Status vocabulary

- `DRAFT`: Bản nháp.
- `PENDING_REVIEW`: Chờ kiểm tra.
- `IN_REVIEW`: Đang kiểm tra.
- `APPROVED`: Đã phê duyệt.
- `PUBLISHED`: Đã công bố.
- `REJECTED`/`NEEDS_CORRECTION`: Đã từ chối/cần hiệu chỉnh.

Không dùng chỉ màu. Mỗi status dùng text, Lucide icon và accessible label.

## 6. Capability và permission

Frontend vẫn dùng permission/capability abstraction tập trung. Phase 0 role là
contract nội bộ, không được trình bày như authentication thật. Unknown
capability fail closed và UI nói `Chưa hỗ trợ` hoặc `Đang chuẩn bị`.

## 7. API và schema

- Frontend chỉ gọi API client abstraction.
- Không gọi filesystem hoặc đọc `outputs`.
- Canonical 14-column schema đến từ `/api/v1/system/schema`.
- Browser chỉ gọi same-origin `/api/v1`.
- Thông tin kỹ thuật không xuất hiện trong copy của người dùng thông thường.

## 8. Visual language

Canonical rules nằm tại:

- `UI_DESIGN_SYSTEM.md`;
- `LEGAL_UI_REFERENCE_PRINCIPLES.md`;
- `VISUAL_QA_CHECKLIST.md`.

Thiết kế dùng system font stack, navy/burgundy/gold tiết chế, border rõ, radius
nhỏ và shadow nhẹ. Không remote font/image, gradient, glass, neon hoặc
official emblem/logo.

## 9. Accessibility foundation

- Semantic `nav`, `main`, skip link.
- `aria-current` cho route active.
- Visible focus.
- Form control có label.
- Icon trang trí `aria-hidden`.
- Icon-only button có accessible name.
- Status có text + icon.
- Heading theo thứ bậc.

Static/DOM tests không thay visual/assistive-technology audit của Project Owner.

## 10. Dữ liệu minh họa

UI/test/screenshot chỉ dùng dữ liệu minh họa tối thiểu. Không dùng tên người,
địa chỉ, CCCD/CMND, case detail, wording hoặc filename lấy từ dữ liệu thật.
Dữ liệu minh họa chỉ chứng minh bố cục/contract, không chứng minh chất lượng xử
lý tài liệu.
