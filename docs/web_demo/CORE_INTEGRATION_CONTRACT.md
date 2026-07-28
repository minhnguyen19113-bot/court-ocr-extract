# Contract tích hợp core pipeline

## 1. Quyền sở hữu

Core pipeline tiếp tục sở hữu:

- chuẩn hóa trang, preprocess và Surya OCR;
- OCR cache;
- phân vùng `front_pre_content` và `decision_tail`;
- deterministic extraction, evidence và validation;
- business rule cho charge, sentence, address, role;
- canonical `FINAL_EXCEL_COLUMNS`.

Web platform sở hữu orchestration nghiệp vụ sau extraction: job metadata, snapshot, review, approval, publishing, export/form capability và UI. Web không sửa, fork hoặc copy parser core.

## 2. Canonical schema

Nguồn thực thi duy nhất của `FINAL_EXCEL` criminal:

`src/court_ocr_extract/final_excel_schema.py::FINAL_EXCEL_COLUMNS`

Web backend phải import/derive schema response từ constant này. Frontend đọc `/api/v1/system/schema`; không có danh sách 14 cột độc lập trong TypeScript component.

Schema response mang `schema_id`, `schema_version`, `case_domain`, field metadata và export order. Phase 0 không thay đổi business rule hoặc thứ tự 14 cột.

## 3. Source-region policy

Production extraction chỉ dùng:

- `front_pre_content`;
- `decision_tail`.

Không dùng `middle_excluded`, `NỘI DUNG VỤ ÁN` hoặc `NHẬN ĐỊNH CỦA TÒA ÁN` làm fallback. Web adapter không tự parse OCR text và không được nới source-region policy.

## 4. Integration boundary dự kiến

Core adapter nhận/yêu cầu contract có version, không nhận public filesystem path. Metadata tối thiểu dự kiến:

- document/version ID;
- processing run ID;
- core pipeline/version;
- schema ID/version;
- case domain;
- processing status;
- extraction snapshot payload/reference;
- entity/field stable IDs;
- evidence references;
- warning/diagnostic codes;
- artifact IDs/checksums.

Adapter chuẩn hóa technical envelope, không biến đổi business value. Raw/large artifact ở artifact storage; database/API dùng opaque reference.

## 5. Luồng nhập machine output

```text
core pipeline result
  → CoreIntegrationAdapter validation
  → processing_run
  → immutable extraction_snapshot
  → review_version
```

Adapter chỉ ghi vùng `processing`. Không có direct write hoặc foreign-key shortcut từ machine output sang official `core`.

Mỗi lần chạy lại tạo run/snapshot version mới. Nếu contract/schema version không được hỗ trợ, adapter fail closed và ghi safe diagnostic; không tự đoán mapping.

## 6. Luồng publishing

Only `PublishService` có quyền điều phối chuyển locked approved snapshot thành official data. Service kiểm tra approval, warning, required field status, lock và schema version rồi ghi `published_snapshot` cùng core entities trong một transaction.

Core integration adapter không publish. Confidence score hoặc machine status không thể thay thế approval.

## 7. Error và audit

Error contract dùng code, stage, correlation ID, run/version ID và safe metadata. Không log:

- OCR text;
- field value nhạy cảm;
- tên/địa chỉ/CCCD;
- filename thật;
- internal path.

Retry tạo attempt/run history phù hợp, không ghi đè snapshot cũ. Audit event append-only.

## 8. Domain extensibility

Adapter envelope có `case_domain`. `criminal` là active domain. `civil` và `administrative` chỉ được nhận khi có schema/rule/adapter version được đăng ký rõ; không tái sử dụng criminal mapping bằng giả định.

## 9. Phase 0

Phase 0 chỉ tạo interface/schema/service contract và synthetic test double. Không:

- chạy core pipeline, OCR hoặc PDF;
- gọi LLM/cloud;
- đọc artifact thật;
- sửa parser;
- cung cấp pipeline execution endpoint;
- deploy.

