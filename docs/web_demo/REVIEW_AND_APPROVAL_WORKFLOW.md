# Workflow kiểm tra và phê duyệt

## 1. Mục tiêu

Workflow bảo đảm machine output chỉ là đề xuất có evidence, còn dữ liệu chính thức phải đi qua human review, approval và transaction publish. Review, approval và publishing là ba quyết định khác nhau.

## 2. Trạng thái hồ sơ

| Trạng thái | Ý nghĩa | Có phải official không |
| --- | --- | --- |
| `DRAFT` | Hồ sơ/phiên mới, chưa xử lý | Không |
| `PROCESSING` | Core pipeline đang hoặc được dự kiến chạy | Không |
| `PENDING_REVIEW` | Có extraction snapshot chờ phân công | Không |
| `IN_REVIEW` | Reviewer đang kiểm tra | Không |
| `NEEDS_CORRECTION` | Cần sửa/reprocess trước khi duyệt | Không |
| `REJECTED` | Review/approval bị từ chối | Không |
| `APPROVED` | Review version đã xác nhận và khóa | Chưa; đủ điều kiện xem xét publish |
| `PUBLISHED` | Transaction ghi vào `core` đã commit | Có |
| `ARCHIVED` | Version không còn active nhưng vẫn được bảo toàn | Theo version nguồn |

Mọi transition đi qua validator tập trung. Không cho phép nhảy trực tiếp từ draft/machine/review state sang `PUBLISHED`.

## 3. Field-status contract

Mỗi extracted/reviewed field có trạng thái riêng; `NULL` không đủ diễn đạt lý do thiếu:

| Enum | Ý nghĩa |
| --- | --- |
| `VALUE_PRESENT` | Có giá trị được lưu |
| `NOT_IN_DOCUMENT` | Tài liệu không chứa field |
| `OCR_UNREADABLE` | Vùng nguồn có thể tồn tại nhưng OCR không đọc được |
| `EXTRACTION_FAILED` | Extraction không tạo được giá trị mong đợi |
| `CONFLICTING_EVIDENCE` | Evidence cho các giá trị không nhất quán |
| `PENDING_REVIEW` | Chưa có quyết định của reviewer |
| `REJECTED_VALUE` | Reviewer từ chối machine/reviewed value |
| `NOT_APPLICABLE` | Field không áp dụng cho entity/case này |

Khi `VALUE_PRESENT`, value và evidence/reference phù hợp phải tồn tại. Khi value trống, một missing reason hợp lệ là bắt buộc đối với field đã được xử lý. Ví dụ `HÌNH PHẠT` của bị hại dùng `NOT_APPLICABLE`, không dùng thông báo chung “Thiếu dữ liệu”.

## 4. Dữ liệu field

Machine và human value không ghi đè nhau. Contract tối thiểu:

- `field_id`;
- `field_key`;
- `machine_value`;
- `machine_status`;
- evidence reference;
- `reviewed_value`;
- `review_status`;
- correction reason;
- reviewer ID và timestamp;
- review version;
- schema version.

Review action tạo version/history mới hoặc append correction record. Approved/locked version không được sửa.

## 5. Reviewer workflow

`reviewer` có thể, theo capability:

- xác nhận machine value;
- sửa giá trị và nêu correction reason;
- đánh dấu `NOT_IN_DOCUMENT`;
- đánh dấu `OCR_UNREADABLE`;
- yêu cầu OCR lại/reprocessing;
- đánh dấu `CONFLICTING_EVIDENCE`;
- từ chối giá trị;
- gửi lại xử lý;
- thêm comment không chứa dữ liệu nhạy cảm trong log.

Reviewer làm việc trên một `review_version` cụ thể. Reprocess không thay thế version cũ; nó tạo processing/extraction version mới.

## 6. Approver workflow

`approver` có thể:

- phê duyệt toàn bộ review version;
- từ chối;
- yêu cầu kiểm tra lại một hoặc nhiều field;
- khóa approved review version;
- yêu cầu publish khi mọi guard đạt.

Approval phải ghi actor, timestamp, review version và schema version. `APPROVED` chưa tạo official core data. Chỉ transaction publish thành công mới chuyển sang `PUBLISHED`.

## 7. Điều kiện phê duyệt và publish

Trước approval cần:

- field review hoàn tất theo rule của schema;
- required field có value hoặc missing reason được policy chấp nhận;
- conflict/critical warning được xử lý hoặc từ chối rõ ràng;
- evidence link còn hợp lệ;
- review version hiện hành.

Trước publish cần thêm:

- approval hợp lệ;
- approved snapshot đã khóa;
- không còn critical warning chưa giải quyết;
- schema version được hỗ trợ;
- source không phải machine snapshot;
- idempotency/concurrency guard đạt.

## 8. Quy tắc bốn mắt

Model phải lưu riêng `corrected_by` và `approved_by` để có thể bật quy tắc:

`corrected_by != approved_by`

Phase 0 chưa bắt buộc enforcement quy tắc bốn mắt. Policy này phải là cấu hình/service guard trong tương lai, không bị khóa bởi schema.

## 9. Role và capability

| Role | Capability Phase 0 được mô tả |
| --- | --- |
| `operator` | Xem intake/job và yêu cầu reprocessing theo workflow |
| `reviewer` | Kiểm tra evidence, field status, correction và comment |
| `approver` | Approve/reject/lock và yêu cầu publish |
| `project_admin` | Quản lý policy/config trong phạm vi dự án |
| `system_admin` | Quản trị capability/system metadata |

Phase 0 chỉ khai báo contract; chưa có authentication hoặc authorization thực. UI phải lấy capability tập trung và luôn để backend là nơi thực thi quyền trong phase sau.

## 10. Audit

Các event tối thiểu:

- review assigned/started/completed;
- field confirmed/corrected/rejected;
- reprocess requested;
- approval granted/rejected/reopened;
- snapshot locked;
- publication requested/succeeded/failed.

Audit event append-only ở application layer, chỉ chứa identifier và metadata an toàn. Không cung cấp generic update/delete service cho audit.

## 11. Boundary Phase 0

Phase 0 kiểm thử state-transition và service guard bằng synthetic identifiers. Không có:

- review mutation API public;
- approval/publish thực;
- dữ liệu thật;
- auto-approval theo confidence;
- draft form preview;
- deployment.

