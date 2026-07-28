# Các phase triển khai

## 1. Nguyên tắc

- Mỗi phase chỉ mở capability khi contract, guard và test tương ứng đạt.
- Criminal là domain đầu tiên; civil/admin không được dựng rule giả.
- Machine output không bao giờ đi thẳng vào `core`.
- Không dùng dữ liệu thật trong fixture/demo.
- Core parser/OCR được tích hợp qua adapter, không sửa trong web branch.

## 2. Phase 0 — Architecture foundation, local-only

Mục tiêu Phase 0:

1. Tạo tài liệu architecture/decision thống nhất.
2. Tạo domain contract cho workflow, field status và canonical schema.
3. Tạo SQLAlchemy/PostgreSQL logical-schema model foundation và Alembic foundation.
4. Tạo service guard cho review/publishing.
5. Tạo FastAPI read-only system/capability endpoints.
6. Tạo form-engine contract; mọi adapter chưa `AVAILABLE`.
7. Tạo Next.js application shell nhiều module trong cùng website.
8. Tạo synthetic tests và chạy safe guardrails.

Gates:

- canonical 14-column response được derive từ backend core constant;
- valid/invalid transition được test;
- machine-to-core path bị cấm;
- `APPROVED != PUBLISHED`;
- publish guard và transaction boundary được mô tả/test;
- legacy `.doc = NOT_IMPLEMENTED`, `.docx/.pdf = DECLARED`;
- API không có mutation;
- frontend không đọc filesystem hoặc chứa parser;
- không có real data, OCR/LLM/cloud;
- không deploy.

## 3. Phase 1 — Local workflow implementation có kiểm soát

Chỉ bắt đầu sau khi Phase 0 đạt gates. Phạm vi đề xuất:

- hoàn thiện PostgreSQL migrations/repositories;
- triển khai local synthetic intake/job/review/approval mutation;
- triển khai transaction publishing với synthetic records;
- authentication/authorization local tối thiểu và capability enforcement;
- authorized artifact metadata/download abstraction;
- giữ core adapter ở test-double nếu chưa cần dữ liệu thật.

Phase 1 không tự động bao gồm OCR thật, form generation thật hoặc deployment.

## 4. Phase 2 — Core integration pilot do Project Owner kiểm soát

Điều kiện vào:

- web shell/API/database/review/publish local ổn định;
- privacy, audit, retention và operational checklist được duyệt;
- core adapter contract tương thích version;
- Project Owner phê duyệt pilot.

Project Owner chạy real-data workflow ngoài Codex theo guardrail. Synthetic fixture không được dùng để kết luận chất lượng.

## 5. Phase 3 — Form adapter implementation

Thực hiện theo từng adapter/template có mẫu và yêu cầu nghiệp vụ được cấp:

- proof-of-concept adapter riêng;
- template version/checksum;
- mapping config;
- instruction removal rule;
- format fidelity và official-generation guard;
- review pháp lý/nghiệp vụ trước khi `AVAILABLE`.

Không triển khai đồng loạt 60 form và không dùng form-specific Python logic.

## 6. Phase 4 — Deployment readiness

Chỉ sau phê duyệt riêng:

- threat model và authentication hardening;
- backup/restore, retention, observability;
- migration/rollback rehearsal;
- performance/capacity test;
- secure artifact storage;
- deployment runbook và operational ownership.

Phase 0 không thực hiện hoặc tuyên bố các nội dung này.

## 7. Thứ tự thực hiện Phase 0

```text
Docs/decisions
  → domain contracts + tests
  → database foundation + tests
  → read-only API + tests
  → form contracts + tests
  → frontend shell + tests
  → safe regression/guardrails
```

Không làm end-to-end lớn rồi mới test. Mỗi bước phải giữ working tree trong đúng scope.

## 8. Phase 0.5 — Acceptance audit

Đã hoàn tất:

- audit 140 file Phase 0, không có real-data artifact, secret hoặc absolute user path;
- giữ nguyên core parser/OCR và pin production `surya-ocr==0.20.0`;
- compile toàn bộ 39 SQLAlchemy table và 81 foreign key theo PostgreSQL dialect;
- tạo explicit table migration `0002_phase0_tables`;
- smoke `upgrade → check → downgrade base → upgrade → check` trên PostgreSQL 16.4 synthetic;
- xác nhận 66 web tests, 11 database tests, 12 Surya contract tests và 490 full Python tests.

Gate frontend chưa đạt vì môi trường không có npm. Phase 0.5 có quyết định cuối:
`PARTIAL — ENVIRONMENT BLOCKED`.

## 9. Phase 0.6 — Frontend toolchain acceptance

Chỉ xử lý phần gate còn thiếu: cung cấp Node/npm phù hợp, tạo và review
`package-lock.json`, sau đó chạy npm dependency audit, Vitest, TypeScript, lint và
Next production build. Không mở auth, upload, OCR execution, job/review/publish
mutation hoặc form generation trong phase này.

Kết quả audit ngày 2026-07-24:

- system Node/npm vẫn không tồn tại; Codex không dùng bundled runtime hoặc tự cài;
- chưa tạo lockfile, ESLint config hoặc chạy npm validation;
- đã khóa runtime ownership ở Project Owner và loopback-only boundary;
- đã tạo operating rules, operations runbook, port/network guide, troubleshooting
  catalog và prerequisite helper read-only;
- PostgreSQL compose được harden bind explicit `127.0.0.1`;
- Python/static validation tiếp tục dùng synthetic contract.

Phase 0.6 giữ trạng thái `PARTIAL — ENVIRONMENT BLOCKED`. Không mở Phase 1. Chỉ
tiếp tục frontend toolchain acceptance sau khi Project Owner cung cấp system
Node/npm phù hợp.

### Continuation ngày 2026-07-24

- xác nhận system Node `v24.18.0`, npm `11.16.0`; không dùng bundled runtime;
- npm tạo `package-lock.json` v3, audit không có local dependency/absolute path;
- `npm ci`, 6 Vitest tests, TypeScript, ESLint và Next build 14 trang đều pass;
- Next rewrite same-origin `/api/v1` tới loopback `WEB_API_ORIGIN`, không bật CORS
  và build không cần backend;
- không khởi động Docker, PostgreSQL, Alembic runtime, backend, frontend, browser
  hoặc background service;
- `npm audit` còn 10 advisory; production-only còn 2 high ở `next`/`postcss`.
  Fix được npm đề xuất yêu cầu major upgrade nên không tự chạy audit fix trong
  continuation.

Quyết định continuation:
`PARTIAL — FRONTEND ENVIRONMENT OR VALIDATION BLOCKED`. Blocker chính xác là
production dependency security audit; không mở Phase 1 hoặc local visual QA cho
đến khi có task upgrade/review riêng.

## 10. Phase 0.7 — Frontend dependency security hardening

Hoàn tất ngày `2026-07-27`:

- tạo baseline mới theo từng GHSA/CVE, dependency path, reachability và
  production/dev classification;
- nâng Next `14.2.26 -> 15.5.21`, React/React DOM `18.3.1 -> 19.2.8`,
  Vitest `2.1.8 -> 3.2.6`;
- chuyển ESLint legacy config sang ESLint 10 native flat config để loại high
  advisory trong `minimatch@3`/`brace-expansion@1`;
- pin ba transitive override exact đã kiểm chứng cho esbuild, PostCSS và sharp;
- migrate ba App Router dynamic params sang async contract của Next 15;
- xác nhận full/production npm audit đều `0 vulnerabilities`;
- xác nhận `npm ci`, Vitest 6/6, typecheck, lint, Next production build,
  `tests/web` 71 pass và full Python suite 495 pass;
- không khởi động service, browser, database hoặc mở port.

Quyết định: `PASS — READY FOR PROJECT OWNER LOCAL RUN AND VISUAL QA`.
Phase tiếp theo chỉ là Project Owner local run/browser visual QA. Phase 1 feature
work và public deployment vẫn chưa được phê duyệt.

## 11. Phase 0.8 — Typography và non-tech UX

Phạm vi:

- chuyển typography sang system font stack an toàn cho tiếng Việt;
- rút navigation từ 11 xuống đúng 10 mục nghiệp vụ, bỏ mục “Kiểm tra OCR” trùng;
- tối giản top bar còn một badge thử nghiệm, notification và user placeholder;
- rút dashboard về đúng bốn summary card và hai section phụ;
- chuẩn hóa `PageHeader`, `SummaryCard`, `SectionCard`, `EmptyState`,
  `PrimaryAction`, status/icon và design tokens;
- viết lại placeholder copy theo mô hình trang/hành động/trạng thái/bước tiếp;
- thêm static/DOM contracts, design-system docs và visual-QA checklist.

Boundary không đổi: không mở Phase 1 feature, không chạy service/browser, không
đụng database/migration/core OCR/parser và không dùng dữ liệu thật. Gate Phase
0.8 yêu cầu audit full/production sạch, Vitest/typecheck/lint/build pass, Python
web/full suite và guardrails pass. Sau đó Project Owner tự chạy visual QA.

## 12. Phase 0.9 — Local operations và checkpoint

- thêm PowerShell prerequisite/backend/frontend/start/status/stop scripts với loopback-only contract;
- lưu runtime state/log ngoài Git, cleanup chỉ đúng PID/compose đã sở hữu;
- thêm known-error knowledge base và local guide một lệnh/14 bước;
- thêm PowerShell AST/static guards và text-hygiene gate không tạo patch Git;
- chạy lại toàn bộ frontend/Python/guardrail gate;
- tạo một commit checkpoint Phase 0 và push normal branch `demo-web-platform`.

Phase này không chạy runtime, không mở browser/port, không sửa core OCR/parser, không
dùng dữ liệu thật và không mở Phase 1.

Trạng thái audit ngày 2026-07-28: Project Owner đã giải phóng Next SWC lock.
`npm.cmd ci`, hai audit, Vitest, typecheck, lint, build, Python/static và guardrails
đều đạt. Một checkpoint được commit và normal-push trên `demo-web-platform`.
Quyết định: `PASS — PHASE 0 CHECKPOINT COMMITTED AND PUSHED`.
