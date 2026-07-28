# Bàn giao Web Demo Platform Phase 0

## 1. Trạng thái

Phase 0 đã tạo architecture foundation local-only trên branch `demo-web-platform`. Không có commit/push/merge/rebase và không có deployment.

## 2. Contract đã khóa

- Canonical web schema derive trực tiếp từ `FINAL_EXCEL_COLUMNS` 14 cột.
- Criminal là domain active đầu tiên; civil/admin fail-closed cho đến khi có policy thật.
- Machine output chỉ thuộc `processing`; dữ liệu chính thức chỉ xuất hiện sau review, approval và atomic publish.
- `APPROVED` và `PUBLISHED` là hai trạng thái khác nhau.
- Audit event append-only; artifact lớn nằm ngoài DB và chỉ được tham chiếu bằng opaque ID.
- API Phase 0 có đúng năm GET endpoint dưới `/api/v1`, không có mutation.
- Form generation chính thức chưa khả dụng; `.doc=NOT_IMPLEMENTED`, `docx/pdf=DECLARED`.

## 3. Cấu trúc chính

- `src/court_ocr_extract/domain/`: workflow, field status, schema, audit, publishing và form contracts.
- `src/court_ocr_extract/database/`: SQLAlchemy metadata/models/repository ports cho sáu logical schema.
- `alembic/`: migration environment và baseline tạo logical schemas.
- `src/court_ocr_extract/services/`: service boundary cho artifact, job, review, publish và form.
- `src/court_ocr_extract/web_api/`: FastAPI app/read-only endpoints.
- `apps/web/`: Next.js application shell, routes, features, API clients và frontend tests.
- `tests/web/`: synthetic contract/control-flow tests.

## 4. Gate còn thiếu

- Gate đã đạt: `tests/web` 60/60, full Python suite 484/484, compileall, repo guardrail, architecture guardrail và Alembic head check.
- Node.js/npm không có trên máy hiện tại, nên chưa chạy Vitest, TypeScript check hoặc Next production build.
- Chưa chạy Alembic trên PostgreSQL thật; model foundation mới được kiểm bằng metadata/SQLite schema translation.
- Authentication, session, RBAC enforcement, CSRF, upload, job execution, review mutation, publish mutation và form generation chưa triển khai.
- Chưa có browser/accessibility visual QA.

## 5. Bước tiếp theo an toàn

1. Cài Node.js phù hợp với `apps/web/package.json`, tạo lockfile và chạy `npm test`, `npm run build`.
2. Thêm PostgreSQL test container/database tạm, chạy Alembic upgrade/downgrade và transaction integration tests.
3. Triển khai authentication/RBAC trước mọi mutation.
4. Mở vertical slice intake → processing record bằng synthetic artifact adapter.
5. Sau đó mới mở review/approval/publish mutation và giữ atomic/audit guards.

Mọi real-data workflow và quality acceptance vẫn do Project Owner chạy ngoài Codex.

## 6. Cập nhật Phase 0.5 — 2026-07-24

- PostgreSQL gate đã đạt trên `postgres:16.4-bookworm`: sáu logical schema, 39 bảng,
  81 foreign key, revision hiện tại `0002_phase0_tables`, không có Alembic drift.
- Downgrade về `base` xóa toàn bộ bảng/schema ứng dụng; upgrade lần hai thành công.
- Publish guard đã test rõ các trạng thái bị cấm `DRAFT`, `PROCESSING`,
  `PENDING_REVIEW`, `IN_REVIEW`, `REJECTED`; official form vẫn chỉ nhận locked
  approved/published source.
- `tests/web`: 66 pass; database targeted: 11 pass; Surya targeted: 12 pass; full
  Python suite: 490 pass, 1 deprecation warning từ Starlette/httpx compatibility.
- Core parser/OCR không đổi. Điều chỉnh Surya test chỉ mock installed distribution
  version để đi đúng nhánh import-failure contract; assertion và production pin không đổi.
- Frontend vẫn bị chặn: system không có Node/npm; bundle có Node `v24.14.0` nhưng
  không có npm. Chưa có `package-lock.json`, chưa chạy Vitest/typecheck/lint/build.

Kết luận Phase 0.5: `PARTIAL — ENVIRONMENT BLOCKED`. Bước kế tiếp duy nhất là
Phase 0.6 frontend toolchain acceptance; chưa được mở Phase 1.

## 7. Cập nhật Phase 0.6 — 2026-07-24

- Branch/worktree vẫn đúng; không có Git operation dang dở.
- `where.exe node`, `where.exe npm`, `node --version`, `npm --version` đều xác nhận
  system Node/npm chưa tồn tại. Không dùng Codex Desktop bundle.
- Vì runtime bị chặn, không chạy `npm install`, không tạo `package-lock.json`, không
  thêm ESLint chưa thể validate và không chạy Vitest/typecheck/lint/build.
- Root `AGENTS.md` đã trỏ tới `CODEX_OPERATING_RULES.md`: Codex chỉ sửa code/docs và
  chạy test hữu hạn; Project Owner trực tiếp vận hành mọi service/browser/network.
- Đã tạo `OPERATIONS_RUNBOOK.md`, `PORTS_AND_NETWORK.md`,
  `TROUBLESHOOTING.md` và helper prerequisite read-only.
- PostgreSQL compose bind đã được harden từ implicit all-interface sang
  `127.0.0.1:${WEB_POSTGRES_PORT:-55432}:5432`; không chạy Docker/PostgreSQL trong
  Phase 0.6.
- Static audit xác nhận 13 business route files, 11 sidebar items, root redirect,
  `/api/v1`, synthetic-only UI và accessibility foundation.
- Frontend–backend proxy/CORS chưa được cấu hình. API-dependent panel giữ controlled
  unavailable state; không bật wildcard CORS trong Phase 0.6.

Kết luận: `PARTIAL — ENVIRONMENT BLOCKED`. Blocker duy nhất để tiếp tục Phase 0.6
toolchain acceptance là system Node/npm phù hợp; chưa mở Phase 1 hoặc local visual QA.

Python/static evidence cuối task: prerequisite helper parse pass và chạy read-only
đúng kỳ vọng blocked; frontend static tests 11 pass; `tests/web` 70 pass; full Python
suite 494 pass; compileall pass. Có một Starlette/httpx deprecation warning đã biết.

## 8. Cập nhật Phase 0.6 continuation — 2026-07-24

- System runtime đã có tại `C:\Program Files\nodejs`: Node `v24.18.0`, npm
  `11.16.0`. Shell ban đầu chưa refresh `PATH`; prerequisite helper dùng fallback
  read-only. Không dùng Codex Desktop bundled Node.
- `package.json` chốt `packageManager npm@11.16.0`, engine Node/npm, scripts
  `test`, `typecheck`, `lint`, `build`; ESLint dùng `next/core-web-vitals` và
  `next/typescript`, không có `eslint-disable` mới.
- npm đã tạo `package-lock.json` v3. Lock chỉ dùng `registry.npmjs.org`, không có
  `file:`/`link:` dependency, absolute user path hoặc credential. `npm ci` pass.
- Vitest 6/6, TypeScript, ESLint `--max-warnings=0` và Next production build 14
  trang đều pass. Build không gọi backend. JSX automatic được khai báo ở Vitest;
  hai assertion accessibility được sửa để truy vấn đúng accessible element.
- Browser API prefix là `/api/v1`; Next rewrite tới server-only
  `WEB_API_ORIGIN=http://127.0.0.1:8000`. Chỉ exact loopback HTTP origin được phép,
  FastAPI không bật CORS và public deployment vẫn `NOT APPROVED`.
- Không chạy Docker/PostgreSQL/Alembic runtime, dev/backend server, browser, OCR,
  cloud/LLM hoặc process nền.
- Full `npm audit`: 1 critical, 6 high, 3 moderate; production audit: 2 high
  (`next` và transitive `postcss`). npm chỉ đề xuất major upgrade để xử lý đầy đủ,
  nên không chạy `npm audit fix`/`--force` và không tự nâng major.

Kết luận continuation:
`PARTIAL — FRONTEND ENVIRONMENT OR VALIDATION BLOCKED`. Frontend functional gates
đã đạt; blocker còn lại là production dependency security audit. Bước tiếp theo
chỉ là task upgrade/security review riêng, chưa mở Phase 1.

## 9. Cập nhật Phase 0.7 — 2026-07-27

- Baseline được chạy lại từ lockfile cũ: full audit có 21 package-node
  (1 critical, 17 high, 3 moderate), production có 2 high. Chi tiết 38 GHSA/CVE
  nằm trong `FRONTEND_DEPENDENCY_SECURITY.md`.
- Nâng exact `next@15.5.21`, `react@19.2.8`, `react-dom@19.2.8`,
  `vitest@3.2.6`; đồng bộ React/Node types.
- ESLint legacy tree được thay bằng native flat config với `eslint@10.8.0`,
  `@eslint/js@10.0.1`, `@next/eslint-plugin-next@15.5.21`,
  `eslint-plugin-react-hooks@7.1.1` và `typescript-eslint@8.65.0`.
- Ba override exact có dependency-path rationale và điều kiện gỡ:
  `esbuild@0.28.1`, `postcss@8.5.23`, `sharp@0.35.0`.
- Ba dynamic route pages dùng async `params` theo Next 15. UI information
  architecture, 13 business routes, 11 sidebar destinations và same-origin API
  rewrite không đổi.
- Final full audit và production audit đều exit `0`, không còn vulnerability.
  `npm ci`, Vitest 6/6, typecheck, lint và Next build đều pass.
- Python compileall pass; `tests/web` 71 pass; full suite 495 pass, còn một
  Starlette/httpx deprecation warning đã biết.
- Không chạy Docker, PostgreSQL, Alembic runtime, backend/frontend server,
  browser, OCR, LLM/cloud, process nền hoặc mở port.

Kết luận Phase 0.7:
`PASS — READY FOR PROJECT OWNER LOCAL RUN AND VISUAL QA`. Local visual QA chưa
được Codex chạy; Project Owner tiếp tục sở hữu mọi runtime operation. Kết luận
này không phê duyệt public/LAN deployment hoặc mở Phase 1 feature work.

## 10. Cập nhật Phase 0.8 — 2026-07-28

- UI dùng system font stack `"Segoe UI", "Noto Sans", Arial, sans-serif`; không
  remote font hoặc image URL.
- Sidebar rộng `264px`, đúng 10 mục và không còn mục “Kiểm tra OCR”. Route động
  và capability nội bộ vẫn giữ nguyên.
- Top bar chỉ có một `Bản thử nghiệm`, notification button và
  `Người dùng thử nghiệm`.
- Dashboard có đúng bốn summary card, một note `Dữ liệu minh họa`, hai section
  `Công việc cần xử lý`/`Lối tắt`.
- Exact `lucide-react@1.27.0` chuẩn hóa icon; không dùng official emblem/logo.
- Placeholder pages dùng wording phổ thông, đúng một primary action và bước
  tiếp theo; action chưa khả dụng disabled.
- Canonical UI docs: `UI_DESIGN_SYSTEM.md`,
  `LEGAL_UI_REFERENCE_PRINCIPLES.md`, `VISUAL_QA_CHECKLIST.md` và
  `UI_INFORMATION_ARCHITECTURE.md`.
- Static contracts Phase 0.8 nằm tại
  `tests/web/frontend/test_phase08_ui_contract.py`; DOM tests bảo vệ shell,
  navigation, dashboard, forms và status.
- Main-workspace frontend validation pass: `npm ci`, hai audit
  `0 vulnerabilities`, Vitest `6/6`, typecheck, lint và build 14 trang. Python
  compileall pass, `tests/web` 108 pass, full suite 532 pass; guardrails pass.
- Lần đầu clean install gặp `EPERM` vì dev server có trước task khóa Next SWC.
  Codex không dừng runtime; khi process tự kết thúc, main-workspace rerun pass và
  generated directories được dọn.

Runtime boundary không đổi: Codex không chạy Docker, PostgreSQL, Alembic runtime,
FastAPI, Next dev server, browser, OCR/LLM/cloud hoặc mở port. Project Owner tự
chạy 13 route và gửi screenshot/issues theo `VISUAL_QA_CHECKLIST.md`. Visual
render chưa được Codex xác nhận bằng browser.

## 11. Cập nhật Phase 0.9 — 2026-07-28

- Có sáu script canonical tại `scripts/web_demo/` cho prerequisite, backend,
  frontend, start, status và stop.
- `start_local.ps1` fail-fast, hỗ trợ `-InstallDependencies`, `-SkipDatabase`,
  `-SkipMigration`; runtime state/log nằm ngoài Git dưới `%LOCALAPPDATA%`.
- `status_local.ps1` read-only; `stop_local.ps1` chỉ xử lý exact PID trong state và
  compose web demo, không broad kill.
- Runbook canonical: `LOCAL_RUN_GUIDE.md` và `KNOWN_ISSUES_AND_RECOVERY.md`.
- Không dùng git diff trong web worktree vì gây chậm/khựng trên máy Project Owner.
- Codex chỉ parse/test tĩnh các script; Project Owner là người duy nhất gọi start,
  status/stop runtime, Docker, migration, server và browser.
- PowerShell/static contract `19 passed`; Python web/full `123/547 passed`; compileall,
  repo guard, architecture guard, text hygiene và hai npm audit PASS.
- Project Owner đã giải phóng Next SWC lock. `npm.cmd ci`, hai audit
  `0 vulnerabilities`, Vitest `6/6`, typecheck, lint và build 14 trang đều PASS.
- Codex không kill process và không chạy runtime; checkpoint chuyển sang
  một commit normal-push trên riêng `demo-web-platform`.
- Quyết định: `PASS — PHASE 0 CHECKPOINT COMMITTED AND PUSHED`.
