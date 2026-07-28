# Security, privacy và audit

## 1. Mức bảo đảm Phase 0

Phase 0 là local-only architecture foundation. Chưa triển khai authentication, authorization, upload, download, OCR, publishing hoặc generation thật. Vì vậy Phase 0 không được mô tả là secure production deployment.

Các contract dưới đây là điều kiện thiết kế cho implementation sau; mọi runtime capability chưa có phải fail closed.

## 2. Data minimization

Không dùng dữ liệu thật trong:

- test và fixture;
- database seed;
- mock API và frontend placeholder;
- screenshot và Storybook;
- README/runbook;
- form definition synthetic.

Không dùng tên, địa chỉ, CCCD/CMND, case detail, wording hoặc filename lấy từ người/tài liệu thật. Synthetic data chỉ phục vụ schema/control-flow và không dùng để đánh giá OCR/extraction quality.

## 3. Logging

Không log:

- họ tên;
- địa chỉ;
- CCCD/CMND;
- OCR text;
- reviewed/machine field value nhạy cảm;
- filename thật nhạy cảm;
- internal artifact path;
- secret/credential.

Log/audit dùng opaque identifier, event type, status, timestamp, actor ID, correlation ID, version và error code đã lọc. Exception handling phải sanitize message trước khi ghi log.

## 4. Artifact security

- Artifact directory không được public trực tiếp.
- Public API không trả filesystem path hoặc internal storage key.
- Artifact được tham chiếu bằng opaque `artifact_id`.
- Download trong phase sau phải qua authorized endpoint, capability check và audit.
- Metadata cần checksum, MIME type, size, type, version và retention state.
- Content-type/extension không đủ để tin cậy; validation chi tiết thuộc phase triển khai upload.

Phase 0 không có upload/download thật.

## 5. Role contract

| Role | Boundary dự kiến |
| --- | --- |
| `operator` | Intake/job operation, không tự approve/publish |
| `reviewer` | Review/correction/evidence |
| `approver` | Approval, lock và publish request |
| `project_admin` | Project-scoped configuration/capability |
| `system_admin` | System administration |

Authentication/authorization chưa được triển khai. UI role placeholder không phải security control. Khi có mutation, backend phải enforcement capability tập trung và default deny.

Model lưu riêng reviewer/corrector/approver để hỗ trợ separation of duties và quy tắc bốn mắt.

## 6. Audit event contract

`audit_event` là append-only ở application layer. Không cung cấp generic update/delete service hoặc API.

Metadata tối thiểu:

- `event_id`;
- `event_type`;
- `occurred_at`;
- actor ID và role/capability context;
- target aggregate type/ID/version;
- correlation ID;
- outcome/error code;
- safe metadata allowlist;
- previous-event/hash reference nếu policy sau yêu cầu tamper evidence.

Không lưu full before/after field value trong audit payload chung. Correction history có versioned domain record riêng, được truy cập theo quyền.

## 7. Event coverage

Thiết kế event cho:

- intake/document version;
- processing run/step;
- review assignment và field decision;
- correction/reprocess request;
- approval/rejection/lock;
- publish request/success/failure;
- export/download;
- form-generation request/result;
- configuration/template version change.

Publication success event phải cùng transaction với published state hoặc có cơ chế bảo đảm atomicity tương đương. Failure event không được làm thay đổi approved snapshot.

## 8. Immutability và versioning

Không ghi đè:

- machine snapshot;
- locked approved review;
- published snapshot;
- template version;
- generated document version;
- audit event.

Mutation hợp lệ tạo version/history mới. Update/delete tùy ý đối với official/audit record bị cấm ở service boundary.

## 9. Secret và configuration

Config mẫu chỉ có placeholder:

- `DATABASE_URL=`
- `ARTIFACT_ROOT=`
- `WEB_API_HOST=`
- `WEB_API_PORT=`
- `FRONTEND_API_BASE_URL=`

Không commit credential, token, private key hoặc endpoint có secret. Phase 0 không tự thay đổi machine-wide configuration.

## 10. API và frontend boundary

- API Phase 0 read-only.
- Frontend không truy cập filesystem, database hoặc core parser.
- Unknown/disabled capability fail closed.
- Không hard-code permission rải rác.
- Error response không phản chiếu input nhạy cảm.
- Không expose OpenAPI example chứa dữ liệu thật.
- CORS, CSRF, rate limit, session và secure header cần được chốt trước khi có deployment/mutation; chưa tuyên bố hoàn tất ở Phase 0.

## 11. Retention và deletion

Artifact metadata có `retention_state`; policy retention/deletion cụ thể chưa được chốt. Phase 0 không tạo delete workflow. Mọi cleanup dữ liệu thật trong tương lai cần Project Owner phê duyệt và audit phù hợp.

## 12. Boundary với core và cloud

- Không sửa hoặc copy core parser/OCR.
- Không chạy Surya, Local LLM hoặc cloud.
- Cloud adapter giữ opt-in/disabled theo core policy.
- Không đọc real PDF hoặc derived real-data artifact.
- Core integration trao đổi versioned contract và opaque artifact reference.

