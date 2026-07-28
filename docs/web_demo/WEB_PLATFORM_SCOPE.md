# Phạm vi nền tảng web demo

## 1. Mục tiêu sản phẩm

Nền tảng web là một website nghiệp vụ thống nhất gồm hai phân hệ:

1. Tiếp nhận, theo dõi xử lý, kiểm tra, phê duyệt, công bố và xuất dữ liệu trích xuất.
2. Soạn biểu mẫu từ dữ liệu đã được phê duyệt hoặc đã được công bố.

Phase 0 xây nền kiến trúc và contract để hai phân hệ dùng chung định danh, quyền, version, audit và nguồn dữ liệu. Phase 0 không phải một luồng `upload → OCR → download`, không phải hệ thống production và không triển khai xử lý tài liệu thật.

## 2. Phạm vi nghiệp vụ

- Domain đang hoạt động: `criminal`.
- Domain dự kiến mở rộng: `civil`, `administrative`.
- Kiến trúc phải cho phép mỗi domain có schema, rule, workflow và form catalog riêng.
- Không triển khai nghiệp vụ dân sự hoặc hành chính trong Phase 0.
- Không sao chép hoặc chuyển parser nghiệp vụ vào frontend hay web API.

`case_domain` và `schema_version` phải xuất hiện tại các boundary phù hợp. Component dùng contract/registry theo domain; không rải điều kiện `if criminal` xuyên suốt hệ thống.

## 3. Contract dữ liệu canonical

Export `FINAL_EXCEL` của domain `criminal` có đúng 14 cột. Nguồn chuẩn duy nhất hiện tại là:

`src/court_ocr_extract/final_excel_schema.py::FINAL_EXCEL_COLUMNS`

Backend sẽ công bố contract này qua API schema. Frontend không duy trì một bản danh sách 14 cột độc lập. Excel chỉ là export view; database không được mô hình hóa thành một bảng phẳng giống file Excel.

## 4. Nội dung Phase 0

Phase 0 bao gồm:

- tài liệu kiến trúc, workflow, API, UI, form engine, security và runbook;
- domain contract cho workflow, field status và canonical schema;
- database/model foundation trên một PostgreSQL với các logical schema;
- service guard cho review, approval, publishing và official form generation;
- FastAPI read-only system endpoints dưới `/api/v1`;
- Next.js application shell nhiều module bằng tiếng Việt;
- form-engine interface và capability contract;
- synthetic fixtures và test cho schema/control-flow;
- migration foundation và repository abstraction.

Phase 0 chỉ chạy local trên máy phát triển. Không deploy và không yêu cầu máy ảo.

## 5. Ngoài phạm vi Phase 0

Phase 0 không triển khai:

- authentication hoặc authorization thực;
- upload PDF/ảnh thực;
- OCR, preprocess, Surya inference hoặc pipeline execution thực;
- đọc thư mục artifact/output trực tiếp từ frontend;
- publish ghi PostgreSQL production;
- download artifact thực;
- form generation thực;
- binary `.doc` parsing/editing;
- LibreOffice automation hoặc chuyển đổi định dạng ngầm;
- tích hợp Local LLM, cloud LLM hoặc cloud OCR;
- catalog/mapping giả cho khoảng 60 biểu mẫu;
- triển khai civil/admin;
- deployment, hardening production hoặc real-data pilot.

## 6. Quy tắc nguồn dữ liệu

- Machine output luôn là dữ liệu nháp và không được ghi trực tiếp vào `core`.
- Dữ liệu machine và dữ liệu human-reviewed được lưu riêng.
- Luồng chính thức là `draft → review → approved → published`.
- `APPROVED` không đồng nghĩa với `PUBLISHED`.
- Publish phải là một transaction: hoặc ghi đầy đủ snapshot đã duyệt cùng audit publication, hoặc rollback toàn bộ.
- Official form generation chỉ nhận approved snapshot hoặc published data.
- Draft preview không được hỗ trợ trong Phase 0.

## 7. Dữ liệu và fixture

Chỉ dùng dữ liệu synthetic tối thiểu cho schema/control-flow. Không dùng dữ liệu thật trong:

- test, fixture hoặc database seed;
- mock API, screenshot hoặc Storybook;
- README, tài liệu hướng dẫn hoặc placeholder frontend.

Synthetic fixture không được dùng để đánh giá chất lượng OCR hoặc extraction.

## 8. Vai trò contract

Phase 0 khai báo các role:

- `operator`: tiếp nhận và theo dõi phiên xử lý;
- `reviewer`: kiểm tra evidence, xác nhận hoặc chỉnh sửa field;
- `approver`: phê duyệt, khóa review version và yêu cầu publish;
- `project_admin`: quản lý cấu hình trong phạm vi dự án;
- `system_admin`: quản trị nền tảng.

Đây là capability contract, chưa phải authentication/authorization thật. Quyền được tập trung trong một permission abstraction, không hard-code rải rác ở UI.

## 9. Tiêu chí hoàn tất phạm vi

Một hạng mục chỉ được coi là thuộc Phase 0 khi:

- giữ nguyên core parser/OCR;
- không truy cập dữ liệu thật;
- không tuyên bố capability chưa triển khai là `AVAILABLE`;
- có contract/test tương ứng cho hành vi an toàn;
- không phát sinh public path tới filesystem hoặc artifact storage;
- chạy local, không deploy;
- giữ khả năng mở rộng domain mà không làm suy yếu criminal-first.

