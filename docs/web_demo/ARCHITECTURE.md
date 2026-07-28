# Kiến trúc nền tảng web demo

## 1. Nguyên tắc kiến trúc

1. `criminal-first`, nhưng domain-extensible.
2. Extraction và form generation nằm trong cùng một website.
3. Core pipeline là nguồn nghiệp vụ; web tích hợp qua contract, không copy parser.
4. Machine, review và official core là ba vùng dữ liệu tách biệt.
5. Approved snapshot là immutable input của transaction publish.
6. File lớn nằm ngoài database; API chỉ trao đổi opaque identifier.
7. Canonical schema có một nguồn backend duy nhất.
8. Phase 0 là local-only, read-only ở API và synthetic-only.

## 2. Các khối chính

```text
Next.js application shell
        |
        | HTTPS/JSON contract trong tương lai
        v
FastAPI /api/v1 (read-only trong Phase 0)
        |
        +-- Domain contracts và workflow guards
        +-- Services: review, publish, form, artifact
        +-- Core integration adapter
        +-- Repository abstractions
                    |
                    +-- Một PostgreSQL
                    |     ingest
                    |     processing
                    |     review
                    |     core
                    |     forms
                    |     audit
                    |
                    +-- Artifact storage nội bộ ngoài DB
```

Phase 0 có thể dùng SQLite cho metadata/unit test. SQLite không phải runtime database của demo hoặc production.

## 3. Frontend

Frontend dùng Next.js, React, TypeScript và App Router. Một application shell cung cấp:

- navigation 10 mục nghiệp vụ và top bar dùng chung;
- các module intake, jobs, data review, publishing, exports, forms, audit, admin và help;
- API client abstraction;
- schema client đọc canonical schema từ backend;
- capability/permission abstraction;
- status component phân biệt draft, pending review, approved, published, unofficial và official.

Phase 0.8 dùng system font stack an toàn cho tiếng Việt, exact
`lucide-react@1.27.0`, dashboard bốn summary card và non-tech placeholder copy.
Không có remote font/image, official emblem/logo hoặc mục `Kiểm tra OCR` trong
navigation chính. Route/job detail vẫn giữ capability nội bộ cho phase tích hợp
sau.

Frontend không:

- gọi filesystem path;
- đọc trực tiếp artifact/output directory;
- chứa OCR, parser hoặc publish logic;
- hard-code danh sách 14 cột hay role permission trong từng component;
- tạo một app riêng cho form generation.

## 4. Backend API

FastAPI dùng versioned prefix `/api/v1`. Phase 0 chỉ cho phép các endpoint read-only:

- `GET /api/v1/system/health`
- `GET /api/v1/system/capabilities`
- `GET /api/v1/system/schema`
- `GET /api/v1/system/workflows`
- `GET /api/v1/forms/capabilities`

Không có endpoint upload, execute OCR, review mutation, publish mutation, artifact download hoặc generation thật trong Phase 0.

## 5. Domain và service

Domain layer sở hữu:

- workflow state/transition;
- field-status enum;
- canonical schema response;
- form-engine interfaces;
- capability và policy value objects.

Service layer điều phối use case và guard. Repository abstraction tách domain/service khỏi persistence. Route không được chứa business rule.

`PublishService` phải kiểm tra approved snapshot, approval, critical warning, required field status, snapshot lock và schema version trước khi mở transaction. Việc triển khai service guard không đồng nghĩa Phase 0 có public write endpoint.

## 6. Database và artifact

Một PostgreSQL được phân vùng logic bằng các schema:

| Logical schema | Trách nhiệm |
| --- | --- |
| `ingest` | Job, document, document version, page, artifact metadata |
| `processing` | Processing run, step, extraction snapshot, entity, field, evidence, warning |
| `review` | Task, version, field review, correction, comment, approval |
| `core` | Published snapshot và dữ liệu nghiệp vụ chính thức |
| `forms` | Catalog, template/version, definition/mapping, generation request/result metadata |
| `audit` | Append-only event và lịch sử publication/export/generation |

PDF, ảnh, OCR cache, HTML, Excel, JSON artifact, DOC/DOCX/PDF và ZIP nằm ở artifact storage nội bộ. Database chỉ lưu metadata, checksum, size, MIME type, version, retention state và opaque reference. Public API không trả storage key/path hoặc đường dẫn phụ thuộc hệ điều hành.

## 7. Luồng dữ liệu

```text
source document version
  → processing run
  → machine extraction snapshot
  → review version
  → locked approved snapshot
  → transactional published snapshot
  → official core entities
  → generated document version
```

Mỗi lần chạy lại tạo version mới. Không ghi đè machine extraction, approved review hoặc published snapshot cũ. Machine value và reviewed value được bảo toàn riêng.

## 8. Boundary với core pipeline

Core pipeline tiếp tục sở hữu:

- preprocess và Surya OCR;
- source-region segmentation;
- deterministic extraction;
- evidence validation;
- canonical `FINAL_EXCEL_COLUMNS`;
- business rules hiện có.

Web branch không sửa parser/OCR và không dùng `middle_excluded` làm fallback. Khi tích hợp sau Phase 0, adapter nhận output có version của core và chuyển thành processing snapshot; adapter không được ghi vào `core`.

## 9. Mở rộng domain

Mỗi domain được nhận diện bằng `case_domain` và tham chiếu:

- `schema_id`/`schema_version`;
- workflow policy;
- validator set;
- form catalog;
- UI capability.

Phase 0 chỉ đăng ký `criminal` là active. `civil` và `administrative` chỉ được công bố là future domain, không có schema/rule giả.

## 10. Boundary vận hành Phase 0

- Chạy local trên máy phát triển.
- Không deploy.
- Không yêu cầu GPU, Docker GPU hoặc máy ảo.
- Không gọi OCR, LLM hoặc cloud.
- Không sử dụng tài liệu thật.
- Authentication, authorized download và persistence mutation chỉ là contract cho phase sau.
