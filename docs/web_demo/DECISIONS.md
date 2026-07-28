# Quyết định kiến trúc web demo

## Trạng thái

- `Accepted`: áp dụng cho Phase 0.
- `Deferred`: cần quyết định/triển khai ở phase sau.
- `Superseded`: đã được quyết định mới thay thế.

## Decision log

| ID | Trạng thái | Quyết định | Lý do/hệ quả |
| --- | --- | --- | --- |
| WEB-D001 | Accepted | Nền tảng `criminal-first` và domain-extensible qua `case_domain`, schema/workflow/form policy có version. | Phase 0 chỉ active criminal; không khóa kiến trúc và không dựng giả civil/admin. |
| WEB-D002 | Accepted | Extraction và form generation nằm trong cùng một Next.js website/application shell. | Dùng chung navigation, permission, version, audit và nguồn dữ liệu. |
| WEB-D003 | Accepted | Web tích hợp core qua adapter/service contract, không sửa/copy parser hoặc OCR. | Core giữ quyền sở hữu business rule và source-region policy. |
| WEB-D004 | Accepted | Canonical 14 cột lấy từ `src/court_ocr_extract/final_excel_schema.py::FINAL_EXCEL_COLUMNS`. | Backend derive API schema; frontend không hard-code bản độc lập. |
| WEB-D005 | Accepted | Dùng một PostgreSQL với logical schema `ingest`, `processing`, `review`, `core`, `forms`, `audit`. | Đủ separation of concerns nhưng phù hợp giai đoạn demo/triển khai đầu. |
| WEB-D006 | Accepted | File lớn ở artifact storage ngoài DB; public API chỉ dùng opaque `artifact_id`. | Không phình DB và không lộ internal/OS-specific path. |
| WEB-D007 | Accepted | Machine output luôn ở `processing`, không ghi trực tiếp vào `core`. | Official data bắt buộc đi qua review, approval và publishing. |
| WEB-D008 | Accepted | Workflow phân biệt `APPROVED` và `PUBLISHED`; publish là transaction atomic. | Approval chưa tạo official record; lỗi publish rollback toàn bộ và giữ approved snapshot. |
| WEB-D009 | Accepted | Snapshot, approved review, published data, template và generated document dùng immutable versioning. | Bảo toàn lineage, reproducibility và audit; retry không ghi đè. |
| WEB-D010 | Accepted | Field status dùng enum `VALUE_PRESENT`, `NOT_IN_DOCUMENT`, `OCR_UNREADABLE`, `EXTRACTION_FAILED`, `CONFLICTING_EVIDENCE`, `PENDING_REVIEW`, `REJECTED_VALUE`, `NOT_APPLICABLE`. | Không gom mọi trường trống thành một `NULL`/“Thiếu dữ liệu”. |
| WEB-D011 | Accepted | Phase 0 API chỉ có năm endpoint GET dưới `/api/v1`; không có mutation. | Tránh giả lập upload/OCR/review/publish/generation khi persistence/security chưa sẵn sàng. |
| WEB-D012 | Accepted | Form definition/mapping là versioned data/config, không có Python logic riêng cho khoảng 60 form. | Cho phép mở rộng và review template theo từng version. |
| WEB-D013 | Accepted | Capability Phase 0: `legacy_doc = NOT_IMPLEMENTED`, `docx = DECLARED`, `pdf = DECLARED`; official generation không khả dụng. | Không giả vờ binary `.doc` editor/converter hoặc output implementation đã tồn tại. |
| WEB-D014 | Accepted | Official form generation chỉ nhận locked approved snapshot hoặc published data; draft preview unsupported trong Phase 0. | Ngăn machine/unapproved data tạo văn bản chính thức. |
| WEB-D015 | Accepted | Role contract gồm `operator`, `reviewer`, `approver`, `project_admin`, `system_admin`; authentication chưa triển khai. | Chuẩn bị capability model nhưng không tuyên bố security control chưa có. |
| WEB-D016 | Accepted | Audit event append-only, không có generic update/delete service; log chỉ dùng identifier và safe metadata. | Bảo toàn accountability và tránh log dữ liệu nhạy cảm. |
| WEB-D017 | Accepted | Fixture, mock, screenshot, seed và placeholder chỉ dùng synthetic data. | Tuân thủ privacy; synthetic chỉ kiểm tra schema/control-flow, không đánh giá quality. |
| WEB-D018 | Accepted | Phase 0 chạy local-only, không deploy, không yêu cầu GPU/Ezycloudx và không gọi OCR/LLM/cloud. | Giới hạn đúng architecture foundation. |
| WEB-D019 | Accepted | Source extraction production chỉ là `front_pre_content` và `decision_tail`; web không dùng `middle_excluded` fallback. | Giữ nguyên core source policy và evidence boundary. |
| WEB-D020 | Deferred | Enforcement quy tắc bốn mắt `corrected_by != approved_by`. | Model/service contract phải hỗ trợ; Phase 0 chưa bắt buộc bật. |
| WEB-D021 | Deferred | Adapter implementation, fidelity validation và strategy cho `.doc`/`.docx`/PDF. | Chỉ quyết định sau khi có template/yêu cầu nghiệp vụ thật và phase được phê duyệt. |
| WEB-D022 | Deferred | Production authentication, retention, deployment topology và operational SLO. | Không thuộc Phase 0; cần security/operations review riêng. |
| WEB-D023 | Accepted | Alembic Phase 0 dùng hai revision explicit: `0001_phase0_foundation` tạo schema và `0002_phase0_tables` tạo 39 bảng; migration không gọi live model metadata hoặc `metadata.create_all()`. | Giữ lịch sử migration ổn định, reviewable và đã xác nhận upgrade/downgrade/upgrade cùng drift check trên PostgreSQL 16.4 synthetic. |
| WEB-D024 | Accepted | Giữ một `requirements-web.txt` cho FastAPI web API và `remote_worker`; không tạo dependency group riêng trong Phase 0.5. | `remote_worker` không import `streamlit`/`jinja2`; các dependency runtime cần thiết vẫn còn và targeted/full Python suite đều pass. |
| WEB-D025 | Accepted | Frontend acceptance phải dùng npm và lockfile do npm tạo; không tạo `package-lock.json` thủ công hoặc thay bằng pnpm. | Môi trường audit không có npm nên Vitest/typecheck/lint/build được báo `ENVIRONMENT BLOCKED`, không hạ gate. |
| WEB-D026 | Accepted | Service/runtime do Project Owner trực tiếp vận hành; Codex chỉ chuẩn bị code, test hữu hạn và runbook. Local demo mặc định bind `127.0.0.1`, không tự bind `0.0.0.0`, mở firewall, browser hoặc process nền. | Giữ quyền kiểm soát vận hành ở Project Owner; Phase 0.6 chưa có authentication/HTTPS/security review nên network/public deployment là task riêng và chưa được phê duyệt. |
| WEB-D027 | Accepted | Browser dùng same-origin `/api/v1`; Next server rewrite tới server-only `WEB_API_ORIGIN`, mặc định exact `http://127.0.0.1:8000` và fail-closed với non-loopback origin. FastAPI không bật CORS trong Phase 0.6. | Giữ browser contract ổn định, không public backend origin, không cần wildcard CORS; build độc lập backend và local runtime vẫn do Project Owner vận hành. |
| WEB-D028 | Accepted | Frontend dependency contract dùng npm `11.16.0`, lockfile v3 và exact pins hiện tại; không tự chạy `npm audit fix` hoặc nâng major Next/Vitest/ESLint config trong continuation. | `npm ci` và mọi frontend gate pass, nhưng production audit còn 2 high; major security upgrade cần task riêng và Phase 0.6 giữ trạng thái partial. |
| WEB-D029 | Accepted | Phase 0.7 dùng exact `next@15.5.21`, React/React DOM `19.2.8`, Vitest `3.2.6` và ESLint 10 native flat config; pin exact overrides `esbuild@0.28.1`, `postcss@8.5.23`, `sharp@0.35.0` cho các transitive advisory chưa được direct package tự giải quyết. | Full/production audit đều sạch; mỗi override nằm trong dependency range/major đã xác minh, có finite test/build và điều kiện gỡ. ESLint 9 bị loại vì tree `minimatch@3`/`brace-expansion@1` vẫn có high advisory; không dùng blind override hoặc audit fix. |
| WEB-D030 | Accepted | Phase 0.8 dùng system font stack `"Segoe UI", "Noto Sans", Arial, sans-serif`, sidebar đúng 10 mục nghiệp vụ, một trial badge, dashboard bốn summary card và exact `lucide-react@1.27.0`; không remote font/image hoặc official branding. | Ưu tiên typography tiếng Việt và non-tech usability, loại mục OCR trùng cùng copy kỹ thuật khỏi luồng chính, giữ build local độc lập network asset và tạo visual-QA contract rõ cho Project Owner. |
| WEB-D031 | Accepted | Phase 0.9 cung cấp launcher PowerShell cố định, state/log ngoài Git và stop theo exact PID; chỉ Project Owner gọi runtime scripts. | Giảm lỗi thao tác local nhưng giữ runtime ownership, loopback boundary và cleanup có giới hạn. |
| WEB-D032 | Accepted | Không dùng git diff trong web worktree vì gây chậm/khựng trên máy Project Owner. | Dùng status, tracked/untracked listing và text-hygiene gate để kiểm kê/checkpoint mà không làm máy Project Owner khựng. |

## Quy tắc thay đổi decision

Decision mới phải:

- nêu rõ ID và trạng thái;
- không âm thầm thay canonical core contract;
- cập nhật tài liệu liên quan;
- không mở capability runtime nếu chưa có implementation/test;
- không mở rộng Phase 0 sang deployment hoặc real-data processing.
