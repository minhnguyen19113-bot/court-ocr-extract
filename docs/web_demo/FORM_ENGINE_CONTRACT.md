# Contract form engine

## 1. Mục tiêu

Form engine cung cấp nền tảng config-driven để sinh nhiều biểu mẫu mà không viết Python `if/else` riêng cho từng mẫu. Phase 0 chỉ định nghĩa domain model, interface, capability và guard; không sinh file thật và không tạo mapping giả cho khoảng 60 biểu mẫu.

## 2. Nguồn dữ liệu hợp lệ

Official generation chỉ được phép từ một trong hai nguồn:

- locked `APPROVED` snapshot;
- `PUBLISHED` core data.

Machine extraction hoặc unapproved review không được dùng để tạo văn bản chính thức. Draft preview là `UNAVAILABLE` trong Phase 0. Watermark draft có thể được nghiên cứu sau nhưng không được giả lập ở Phase 0.

## 3. Domain concepts

| Concept | Trách nhiệm |
| --- | --- |
| `FormCatalog`/`FormCatalogEntry` | Metadata và domain của biểu mẫu |
| `FormTemplate` | Định danh template ổn định |
| `FormTemplateVersion` | Artifact/checksum/format/version immutable |
| `FormDefinition` | Cấu hình dữ liệu của biểu mẫu |
| `FormFieldDefinition` | Kiểu, label, required/manual/validation |
| `FormFieldMapping` | Nguồn, transform, formatter, placeholder và rule |
| `FormGenerationRequest` | Source/version, template version, format, manual values |
| `GeneratedDocument` | Metadata/version/artifact reference của output |
| `TemplateAdapter` | Interface theo format, không chứa form-specific business rule |
| `SourceResolver` | Đọc field từ approved/published contract |
| `Formatter` | Chuyển value sang presentation đã khai báo |
| `GenerationResult` | Success/failure/warning/artifact metadata an toàn |

`FormDefinition` là data/config có version và validation schema. Không bắt buộc một Python class riêng cho mỗi form.

## 4. Field mapping

Một mapping có thể khai báo:

- `source_field`;
- `source_entity`;
- `source_path`;
- transformation;
- formatter;
- required;
- cho phép manual input;
- default/config value;
- visibility condition;
- repeat rule;
- exclusion rule;
- validation rule;
- output placeholder/bookmark;
- help/instruction removal rule.

Fixed values như tên đơn vị, địa danh, chức danh hoặc thông tin cơ quan phải đến từ versioned configuration, không hard-code source code.

Manual input chỉ áp dụng khi source hợp lệ không có dữ liệu và definition cho phép. Người dùng không phải nhập lại dữ liệu đã có trong approved/core source.

## 5. Exclusion và instruction removal

Nội dung hướng dẫn/chú thích trong template chỉ được loại bỏ bằng rule khai báo theo template version:

- target placeholder/bookmark/region cụ thể;
- điều kiện loại bỏ;
- expected result;
- validation sau loại bỏ;
- warning khi adapter không hỗ trợ.

Không dùng một regex chung không kiểm soát. Nếu adapter không bảo đảm loại bỏ instruction, result không được coi là official và UI phải hiển thị cảnh báo.

## 6. Capability enum

| Trạng thái | Ý nghĩa |
| --- | --- |
| `NOT_IMPLEMENTED` | Contract có nhắc tới nhưng adapter chưa được triển khai |
| `DECLARED` | Output/adapter được thiết kế, chưa có implementation được xác minh |
| `AVAILABLE` | Implementation và guard/test đạt trong runtime hiện tại |
| `UNAVAILABLE` | Capability không dùng được trong environment/policy hiện tại |

Capability status phải phản ánh runtime trung thực, không suy từ extension.

## 7. Adapter matrix Phase 0

| Adapter | Capability | Adapter implemented | Official generation |
| --- | --- | --- | --- |
| `legacy_doc` (`.doc`) | `NOT_IMPLEMENTED` | Không | Không |
| `docx` (`.docx`) | `DECLARED` | Không | Không |
| `pdf` | `DECLARED` | Không | Không |

Không có adapter `AVAILABLE` trong Phase 0. Không dùng LibreOffice automation, không parse/edit binary `.doc`, không chuyển `.doc` sang `.docx` âm thầm và không tuyên bố converter tồn tại.

## 8. Template versioning

Mỗi `FormTemplateVersion` là immutable và gồm:

- template ID/version;
- case domain;
- format;
- artifact ID/checksum;
- definition/mapping version;
- capability requirement;
- effective status;
- created actor/time.

Generation request pin chính xác source version, template version, definition version và output format. Generated document tạo version mới, không ghi đè output cũ.

## 9. Generation request guard

Trước official generation, service phải kiểm tra:

- source state là `APPROVED` hoặc `PUBLISHED`;
- approved source đã khóa;
- source/schema version được hỗ trợ;
- template và definition version tồn tại;
- adapter có `AVAILABLE`;
- required mappings được resolve hoặc manual value hợp lệ;
- exclusion/validation rule đạt;
- actor có capability;
- không còn blocking warning.

Trong Phase 0, guard dừng ở `adapter not available`, vì mọi adapter đều chưa `AVAILABLE`.

## 10. Interface semantics

`TemplateAdapter` dự kiến cung cấp:

- `capabilities()`;
- `validate_template(template_version)`;
- `render(request, resolved_fields)`;
- `validate_result(result)`.

`SourceResolver` chỉ đọc approved snapshot hoặc published projection. Adapter không được truy cập trực tiếp machine tables, filesystem path công khai hay parser.

`GenerationResult` không trả internal path; chỉ trả status, generated-document ID, artifact ID khi có, warnings và metadata an toàn.

## 11. Synthetic contract fixtures

Nếu cần test, chỉ dùng tối đa một vài definition có tên rõ như:

- `SYNTHETIC_CRIMINAL_FORM_A`;
- `SYNTHETIC_CRIMINAL_FORM_B`.

Fixture chỉ kiểm tra schema/control-flow, không đại diện biểu mẫu Tòa án thật và không dùng để đánh giá generation quality.

## 12. Mở rộng domain

Form catalog/definition có `case_domain`. `criminal` là active domain Phase 0; `civil` và `administrative` chỉ là future capability. Không tự đoán template, field hoặc workflow của domain tương lai.

