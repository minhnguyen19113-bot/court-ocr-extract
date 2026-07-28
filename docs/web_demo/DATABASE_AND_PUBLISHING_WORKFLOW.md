# Database và workflow công bố

## 1. Database topology

Giai đoạn demo và triển khai đầu dùng một PostgreSQL, được chia thành sáu logical schema:

| Schema | Các aggregate chính |
| --- | --- |
| `ingest` | `job`, `document`, `document_version`, `document_page`, `artifact` |
| `processing` | `processing_run`, `pipeline_step`, `extraction_snapshot`, `extracted_entity`, `extracted_field`, `evidence_ref`, `extraction_warning` |
| `review` | `review_task`, `review_version`, `field_review`, `field_correction`, `review_comment`, `approval` |
| `core` | `published_snapshot`, `court_case`, `judgment`, `person`, `case_party`, `charge`, `sentence`, `address`, `source_document_link` |
| `forms` | `form_catalog_entry`, `form_template`, `form_template_version`, `form_definition`, `form_field_definition`, `form_field_mapping`, `form_generation_request`, `generated_document` |
| `audit` | `audit_event` |

Identity/access foundation gồm `user`, `role`, `user_role` và nằm trong logical schema `audit` ở Phase 0. Cách đặt này giữ đúng sáu schema đã chốt, cho phép actor reference dùng chung và không tạo shortcut từ machine data sang `core`. Phase 0 yêu cầu boundary và relationship rõ, không yêu cầu hoàn thiện mọi relationship nghiệp vụ.

Database không phải bản sao của sheet `FINAL_EXCEL`. Core entities được chuẩn hóa; export 14 cột là projection có version.

## 2. Định danh và metadata chung

Model cần dùng UUID hoặc stable ID và có, khi phù hợp:

- `created_at`;
- `updated_at`;
- `version`;
- `status`;
- source reference;
- uniqueness/index có giải thích;
- foreign key không vượt boundary sai quy tắc.

Mọi snapshot phải ghi `schema_id`, `schema_version` và `case_domain`. Version dùng optimistic uniqueness phù hợp, ví dụ unique theo `(aggregate_id, version)`.

## 3. Artifact storage

File lớn không lưu trong PostgreSQL:

- PDF/ảnh;
- OCR cache;
- HTML/Excel/JSON;
- DOC/DOCX/PDF sinh ra;
- ZIP.

Artifact storage nội bộ giữ nội dung. Database chỉ lưu:

- `artifact_id`;
- opaque internal storage key;
- checksum;
- MIME type và byte size;
- artifact type;
- quan hệ với job/document/run;
- actor ID và thời điểm tạo;
- version;
- retention state.

API public không trả storage key/path nội bộ hoặc đường dẫn filesystem. Download trong phase sau phải đi qua authorized endpoint tra cứu bằng `artifact_id`.

## 4. Lineage và immutability

Lineage bắt buộc:

```text
document_version
  → processing_run
  → extraction_snapshot
  → review_version
  → approval + locked approved snapshot
  → published_snapshot
  → generated_document
```

Mỗi lần chạy lại pipeline tạo `processing_run` và `extraction_snapshot` mới. Không update in-place:

- machine extraction cũ;
- review version đã approved/locked;
- published snapshot;
- form template version;
- generated document version;
- audit event.

Các version tối thiểu:

- `document_version`;
- `processing_run_version`;
- `extraction_snapshot_version`;
- `review_version`;
- `published_version`;
- `form_template_version`;
- `generated_document_version`.

## 5. Tách machine, reviewed và official data

`processing` giữ machine output. `review` giữ human decision. `core` chỉ giữ dữ liệu đã publish.

Một field review có thể tham chiếu machine field nhưng phải bảo toàn riêng:

- `machine_value`;
- `reviewed_value`;
- `review_status`;
- `correction_reason`;
- `corrected_by`;
- `corrected_at`.

Không sửa `machine_value`. Không có foreign key hoặc service path cho phép machine extraction trở thành official core entity nếu không đi qua locked approved snapshot và `published_snapshot`.

## 6. State workflow

State tổng quát:

```text
DRAFT
  → PROCESSING
  → PENDING_REVIEW
  → IN_REVIEW
      ├─→ NEEDS_CORRECTION → PROCESSING hoặc PENDING_REVIEW
      ├─→ REJECTED
      └─→ APPROVED
              → PUBLISHED
                    → ARCHIVED
```

Transition cụ thể sẽ được validator khai báo tập trung. Tối thiểu phải cấm:

- `DRAFT → PUBLISHED`;
- `PROCESSING → PUBLISHED`;
- `PENDING_REVIEW → PUBLISHED`;
- `IN_REVIEW → PUBLISHED`;
- `REJECTED → PUBLISHED`;
- machine extraction → core;
- official form generation từ unapproved source.

`APPROVED` nghĩa là review version đã được người có quyền xác nhận và khóa. `PUBLISHED` nghĩa là transaction ghi snapshot đó vào `core` đã commit và publication audit event đã được tạo.

## 7. Điều kiện publish

`PublishService` chỉ chấp nhận khi:

- source là approved snapshot, không phải machine snapshot;
- approval tồn tại và actor có capability phù hợp;
- review status là `APPROVED`;
- không còn critical warning chưa giải quyết;
- required fields có field status hợp lệ;
- mọi field trống có missing reason;
- approved snapshot đã khóa;
- `schema_version` tồn tại và được hỗ trợ;
- snapshot chưa được publish trùng theo idempotency key/version.

Confidence score không được dùng để tự động publish.

## 8. Transaction publish

Một transaction publish thực hiện theo thứ tự logic:

1. Khóa/đọc nhất quán approved snapshot và kiểm tra lại precondition.
2. Tạo `published_snapshot` với source lineage và version.
3. Ghi hoặc liên kết các official core entity.
4. Tạo source-document link.
5. Ghi publication audit event an toàn.
6. Commit toàn bộ transaction.

Nếu bất kỳ bước nào lỗi:

- rollback toàn bộ core/publication changes;
- không để official data ở trạng thái một phần;
- approved snapshot vẫn immutable và giữ nguyên;
- lỗi được ghi bằng identifier/metadata an toàn ngoài transaction thất bại hoặc qua cơ chế đáng tin cậy;
- không log field value hay nội dung tài liệu.

## 9. Concurrency và idempotency

Thiết kế model/service cần chuẩn bị:

- unique publication key trên approved snapshot/version;
- idempotency key cho publish request trong phase có write endpoint;
- optimistic version check hoặc row lock;
- trạng thái retry không tạo hai published version giống nhau;
- audit correlation ID không chứa dữ liệu nhạy cảm.

## 10. Boundary Phase 0

Phase 0 tạo metadata/model foundation và test workflow/service guard. Có thể dùng SQLite cho metadata test. Không có:

- PostgreSQL production tự cài;
- public publish endpoint;
- ghi dữ liệu thật;
- migration production đã được vận hành;
- deployment.
