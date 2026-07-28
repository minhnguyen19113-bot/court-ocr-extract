# API contract v1

## 1. Phạm vi

Base prefix: `/api/v1`

Phase 0 chỉ cung cấp read-only system/capability contract. Không có endpoint mutation cho upload, OCR, review, approval, publishing, artifact download hoặc form generation. Service guard có thể được kiểm thử nội bộ nhưng không được hiểu là public API đã sẵn sàng.

Các endpoint Phase 0:

- `GET /api/v1/system/health`
- `GET /api/v1/system/capabilities`
- `GET /api/v1/system/schema`
- `GET /api/v1/system/workflows`
- `GET /api/v1/forms/capabilities`

## 2. Quy ước chung

- Media type: `application/json`.
- Timestamp khi có: UTC, ISO 8601.
- Identifier: opaque stable ID; client không suy diễn nội dung từ ID.
- Enum: uppercase theo contract.
- `schema_version` và `case_domain` được trả rõ khi response phụ thuộc domain.
- Public response không chứa filesystem path, internal storage key, credential hoặc dữ liệu nhạy cảm.
- Phase 0 dùng dữ liệu hệ thống/synthetic; không trả tài liệu hoặc field value thật.

Error response dự kiến:

```json
{
  "error": {
    "code": "CAPABILITY_NOT_AVAILABLE",
    "message": "Chức năng chưa khả dụng trong Phase 0.",
    "correlation_id": "synthetic-correlation-id"
  }
}
```

`correlation_id` không chứa filename, tên người, mã định danh cá nhân hoặc nội dung OCR.

## 3. Health

### `GET /api/v1/system/health`

Mục đích: kiểm tra process API có phản hồi, không kiểm tra OCR/GPU/cloud.

Response tối thiểu:

```json
{
  "status": "ok",
  "service": "court-ocr-web-api",
  "api_version": "v1",
  "environment": "local",
  "persistence": "foundation_only"
}
```

Health không được đọc tài liệu, chạy OCR hoặc tiết lộ dependency secret.

## 4. System capabilities

### `GET /api/v1/system/capabilities`

Response phải phân biệt capability được thiết kế với runtime operation đang khả dụng:

```json
{
  "api_version": "v1",
  "environment": "local",
  "active_case_domains": ["criminal"],
  "future_case_domains": ["civil", "administrative"],
  "input_types_designed": ["pdf", "jpg", "jpeg", "png"],
  "export_types_designed": ["xlsx", "json", "html", "zip"],
  "document_generation_types_declared": ["doc", "docx", "pdf"],
  "ocr_backend": {
    "ownership": "external_core_integration",
    "runtime_available": false
  },
  "supports_review_contract": true,
  "supports_approval_contract": true,
  "supports_publishing_contract": true,
  "supports_form_generation_contract": true,
  "mutation_endpoints_available": false,
  "official_form_generation_source_states": ["APPROVED", "PUBLISHED"],
  "phase": "PHASE_0"
}
```

Danh sách type thể hiện thiết kế contract, không khẳng định upload/export/generation đã chạy. Phase 0 luôn có `mutation_endpoints_available = false`.

## 5. Canonical schema

### `GET /api/v1/system/schema`

Query dự kiến:

- `case_domain`, mặc định duy nhất trong Phase 0 là `criminal`;
- `schema_id` khi có nhiều projection trong tương lai.

Nguồn chuẩn duy nhất của thứ tự cột `FINAL_EXCEL` hiện tại:

`src/court_ocr_extract/final_excel_schema.py::FINAL_EXCEL_COLUMNS`

Backend schema contract phải import/derive từ constant này. Không tạo thêm một danh sách canonical độc lập trong API hoặc frontend.

Response:

```json
{
  "schema_id": "criminal.final_excel",
  "schema_version": "1.0.0",
  "case_domain": "criminal",
  "columns": [
    {
      "key": "LOẠI ÁN",
      "label": "LOẠI ÁN",
      "export_order": 1,
      "required": null,
      "review_rule": "DOMAIN_POLICY"
    }
  ]
}
```

`columns` phải có đủ 14 phần tử theo đúng thứ tự:

1. `LOẠI ÁN`
2. `SỐ BẢN ÁN`
3. `NGÀY TUYÊN ÁN (DD/MM/YYYY)`
4. `SỐ THỤ LÝ`
5. `NGÀY THỤ LÝ (DD/MM/YYYY)`
6. `QUAN HỆ PHÁP LUẬT`
7. `HÌNH PHẠT`
8. `TƯ CÁCH TỐ TỤNG`
9. `HỌ TÊN ĐƯƠNG SỰ`
10. `NĂM SINH`
11. `CCCD`
12. `ĐỊA CHỈ`
13. `HỌ TÊN CHỦ TỌA`
14. `GHI CHÚ`

Danh sách trên là mô tả contract để review; source code backend constant vẫn là nguồn thực thi duy nhất. Không tự đặt mọi cột `required = true`. Metadata required/review phải dùng business policy hiện có hoặc để chưa xác định rõ ràng.

## 6. Workflow contract

### `GET /api/v1/system/workflows`

Response tối thiểu:

```json
{
  "workflow_id": "extraction-review-publishing",
  "workflow_version": "1.0.0",
  "case_domain": "criminal",
  "states": [
    "DRAFT",
    "PROCESSING",
    "PENDING_REVIEW",
    "IN_REVIEW",
    "NEEDS_CORRECTION",
    "REJECTED",
    "APPROVED",
    "PUBLISHED",
    "ARCHIVED"
  ],
  "approved_is_published": false,
  "machine_output_can_publish": false,
  "publish_is_transactional": true,
  "field_statuses": [
    "VALUE_PRESENT",
    "NOT_IN_DOCUMENT",
    "OCR_UNREADABLE",
    "EXTRACTION_FAILED",
    "CONFLICTING_EVIDENCE",
    "PENDING_REVIEW",
    "REJECTED_VALUE",
    "NOT_APPLICABLE"
  ]
}
```

Response thực tế phải kèm transition hợp lệ hoặc policy reference đủ để frontend hiển thị; frontend không tự suy diễn transition.

## 7. Form capabilities

### `GET /api/v1/forms/capabilities`

Capability enum:

- `NOT_IMPLEMENTED`
- `DECLARED`
- `AVAILABLE`
- `UNAVAILABLE`

Response Phase 0 bắt buộc thể hiện:

```json
{
  "contract_supported": true,
  "official_generation_available": false,
  "draft_preview_available": false,
  "source_states_allowed_for_official_generation": [
    "APPROVED",
    "PUBLISHED"
  ],
  "formats": {
    "legacy_doc": {
      "capability_status": "NOT_IMPLEMENTED",
      "adapter_implemented": false,
      "output_format_declared": true
    },
    "docx": {
      "capability_status": "DECLARED",
      "adapter_implemented": false,
      "output_format_declared": true
    },
    "pdf": {
      "capability_status": "DECLARED",
      "adapter_implemented": false,
      "output_format_declared": true
    }
  }
}
```

Không format nào có `AVAILABLE` trong Phase 0. `legacy_doc` không được mô tả là converter hoặc editor đã tồn tại.

## 8. Authentication và permission

Contract role gồm `operator`, `reviewer`, `approver`, `project_admin`, `system_admin`. Phase 0 chưa có authentication/authorization thực. Không dùng role placeholder làm cơ chế bảo vệ. Khi mutation được bổ sung ở phase sau, backend phải kiểm tra capability; UI chỉ dùng capability để trình bày.

## 9. Artifact contract tương lai

API chỉ dùng `artifact_id` và metadata đã lọc. Không trả:

- đường dẫn nội bộ;
- storage key;
- public directory URL;
- tên file thật nhạy cảm.

Authorized download endpoint không thuộc Phase 0 và không được giả lập là đã sẵn sàng.

## 10. Compatibility

- Thay đổi phá vỡ response cần API version hoặc schema version mới.
- Thêm optional field phải giữ client cũ hoạt động.
- Thứ tự `FINAL_EXCEL` chỉ thay đổi khi canonical core contract thay đổi có chủ đích; Phase 0 không thay đổi.
- Frontend cần xử lý capability không biết theo hướng fail closed.

