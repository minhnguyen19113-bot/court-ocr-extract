# Troubleshooting Web Demo Platform

Mỗi mục dùng cùng cấu trúc. Ngày cập nhật: **2026-07-24**.

Không chia sẻ credential, `.env`, `DATABASE_URL`, PDF/ảnh/OCR text, họ tên, địa
chỉ, CCCD/CMND, case detail, artifact path hoặc file thật. Log được phép chia sẻ
phải được sanitize trước.

## WEB-NODE-001 — Node không được nhận diện

- Triệu chứng: `where.exe node` không có kết quả hoặc `node` is not recognized.
- Nguyên nhân có thể: Node chưa cài hoặc PATH của PowerShell chưa refresh.
- Cách kiểm tra: `where.exe node`; `node --version`.
- Cách khắc phục: Project Owner cài bản Node có npm và đáp ứng `engines.node`,
  rồi mở PowerShell mới. Không dùng Node bundle của Codex.
- Kết quả mong đợi: system path rõ ràng và version đáp ứng
  `^20.19.0 || ^22.13.0 || >=24`.
- Log được phép chia sẻ: command, exit code, version và sanitized system path.
- Dữ liệu không được chia sẻ: nội dung `.env`, user profile listing.
- Ngày cập nhật: 2026-07-24.

## WEB-NPM-001 — npm không được nhận diện

- Triệu chứng: `where.exe npm` rỗng hoặc `npm` is not recognized.
- Nguyên nhân có thể: Node distribution thiếu npm hoặc PATH chưa refresh.
- Cách kiểm tra: `where.exe npm`; `npm --version`.
- Cách khắc phục: Project Owner sửa/cài lại Node distribution chính thức có npm;
  không chuyển sang pnpm/yarn và không dùng bundled runtime.
- Kết quả mong đợi: npm có system path và version ổn định để ghi vào
  `packageManager`.
- Log được phép chia sẻ: exit code, npm version, sanitized path.
- Dữ liệu không được chia sẻ: npm token, user-level `.npmrc`.
- Ngày cập nhật: 2026-07-24.

## WEB-INSTALL-001 — npm install thất bại

- Triệu chứng: `npm install` trả non-zero hoặc không tạo lockfile.
- Nguyên nhân có thể: network/registry lỗi, peer conflict, disk/permission hoặc
  Node/npm không tương thích.
- Cách kiểm tra: ghi package name, npm error code và 30 dòng log đã sanitize;
  kiểm tra `node --version`, `npm --version`, `npm config get registry`.
- Cách khắc phục: dùng registry được phê duyệt; sửa exact dependency contract.
  Không dùng `--force`, `--legacy-peer-deps`, `npm update` hoặc `npm audit fix`
  mặc định.
- Kết quả mong đợi: install hoàn tất và tạo `apps/web/package-lock.json`.
- Log được phép chia sẻ: npm error code, package/version, sanitized stack tail.
- Dữ liệu không được chia sẻ: auth token, proxy credential, full `.npmrc`.
- Ngày cập nhật: 2026-07-24.

## WEB-LOCK-001 — package-lock không đồng bộ

- Triệu chứng: `npm ci` báo package.json và lockfile không khớp.
- Nguyên nhân có thể: package.json đổi mà chưa chạy npm install bằng đúng npm.
- Cách kiểm tra: dùng `git status --short`, rồi inspect `lockfileVersion`, registry
  và local path trong đúng hai file.
- Cách khắc phục: với npm version đã chốt, chạy `npm install`, review lockfile,
  rồi chạy lại `npm ci`. Không sửa lockfile thủ công.
- Kết quả mong đợi: `npm ci` pass trên clean `node_modules`.
- Log được phép chia sẻ: dependency name/version và lockfile metadata.
- Dữ liệu không được chia sẻ: registry credential, local absolute user path.
- Ngày cập nhật: 2026-07-24.

## WEB-INSTALL-002 — npm ci không xóa được Next SWC

- Triệu chứng: `npm ci` trả `EPERM unlink` tại
  `next-swc.win32-x64-msvc.node`.
- Nguyên nhân đã xác minh: một `npm run dev`/Next process đang dùng binary trong
  `apps/web/node_modules`.
- Cách kiểm tra: Project Owner xem cửa sổ frontend đang chạy và dừng đúng process
  bằng `Ctrl+C`; không kill hàng loạt.
- Cách khắc phục: sau khi frontend đã dừng, chạy lại `npm ci`. Không dùng
  `--force`, không xóa binary riêng lẻ khi process còn giữ file.
- Kết quả mong đợi: clean install hoàn tất từ lockfile và audit sạch.
- Log được phép chia sẻ: error code, package path tương đối và PID/process name.
- Dữ liệu không được chia sẻ: full process environment, `.env.local`, credential.
- Ngày cập nhật: 2026-07-28.

## Catalog recovery Phase 0.9

Các lỗi launcher/runtime mới dùng mã canonical và quy trình recovery chi tiết tại
`KNOWN_ISSUES_AND_RECOVERY.md`. Bắt đầu bằng `check_prerequisites.ps1` hoặc
`status_local.ps1`; không broad kill process và không chia sẻ log chứa dữ liệu thật.

## WEB-AUDIT-001 — npm audit còn advisory

- Triệu chứng: `npm audit` trả exit code 1 dù install/test/build pass.
- Baseline lịch sử ngày 2026-07-27: full audit có 21 package-node
  (1 critical, 17 high, 3 moderate); audit `--omit=dev` có 2 high. Phase 0.7
  final audit đã sạch.
- Cách kiểm tra: chạy `npm audit` và `npm audit --omit=dev`; chỉ ghi package,
  severity, affected range và fix availability đã sanitize.
- Cách khắc phục: so sánh với `FRONTEND_DEPENDENCY_SECURITY.md`, xác định direct
  owner/dependency path rồi nâng exact version có review. Không chạy
  `npm audit fix`, `npm audit fix --force`, `npm update`, `--force` hoặc
  `--legacy-peer-deps`.
- Kết quả mong đợi: full và production audit cùng exit `0`; nếu critical/high
  quay lại thì không local run/public deploy.
- Log được phép chia sẻ: advisory ID, package/version, severity và fix range.
- Dữ liệu không được chia sẻ: npm token, `.npmrc`, proxy credential.
- Ngày cập nhật: 2026-07-27.

## WEB-TEST-002 — Vitest không load config trong filesystem sandbox

- Triệu chứng: esbuild báo `Cannot read directory` ở parent filesystem và không
  resolve được `vitest.config.ts`.
- Nguyên nhân đã xác minh: filesystem sandbox chặn bước config discovery của
  esbuild trên Windows; không phải failed assertion hay dependency mismatch.
- Cách kiểm tra: chỉ trong môi trường kiểm thử được phê duyệt, chạy cùng finite
  `npm test` ngoài sandbox; không dùng browser/UI/API mode.
- Cách khắc phục: không đổi test script, không thêm skip/xfail và không hạ
  esbuild xuống version có advisory. Giữ `esbuild@0.28.1`.
- Kết quả mong đợi: 6 test files, 6 tests pass, không mở listener.
- Ngày cập nhật: 2026-07-27.

## WEB-TEST-001 — Vitest thất bại

- Triệu chứng: `npm test` có failed test.
- Nguyên nhân có thể: UI contract regression, jsdom/setup lỗi hoặc dependency
  mismatch.
- Cách kiểm tra: chạy lại đúng failed test hữu hạn; ghi test name và assertion.
- Cách khắc phục: sửa source/test đúng contract; không nới assertion, skip hoặc
  xfail để che lỗi.
- Kết quả mong đợi: mọi Vitest test pass.
- Log được phép chia sẻ: test name, assertion diff synthetic, sanitized stack.
- Dữ liệu không được chia sẻ: browser state hoặc dữ liệu nghiệp vụ thật.
- Ngày cập nhật: 2026-07-24.

## WEB-TSC-001 — TypeScript thất bại

- Triệu chứng: `npm run typecheck` trả type error.
- Nguyên nhân có thể: import/type mismatch, server/client boundary hoặc generated
  Next type chưa đồng bộ.
- Cách kiểm tra: ghi file, line, TypeScript error code; không chạy dev server.
- Cách khắc phục: sửa type/source; không dùng `any` hoặc disable strict hàng loạt.
- Kết quả mong đợi: `tsc --noEmit` pass.
- Log được phép chia sẻ: error code và source location không nhạy cảm.
- Dữ liệu không được chia sẻ: `.env.local`, API payload thật.
- Ngày cập nhật: 2026-07-24.

## WEB-LINT-001 — ESLint thất bại

- Triệu chứng: `npm run lint` trả rule violation/config error.
- Nguyên nhân có thể: ESLint config/version không tương thích hoặc source vi
  phạm rule.
- Cách kiểm tra: ghi rule ID, file/line và exact dependency versions.
- Cách khắc phục: sửa source/config tối thiểu; không tắt toàn bộ rule hoặc thêm
  hàng loạt disable.
- Kết quả mong đợi: lint pass cho TypeScript/TSX source.
- Log được phép chia sẻ: rule ID và sanitized source location.
- Dữ liệu không được chia sẻ: secret hoặc generated output.
- Ngày cập nhật: 2026-07-24.

## WEB-BUILD-001 — Next production build thất bại

- Triệu chứng: `npm run build` lỗi compile, route, hydration hoặc boundary.
- Nguyên nhân có thể: import thiếu, client/server misuse, build-time API call hoặc
  TypeScript error.
- Cách kiểm tra: ghi route/module đầu tiên lỗi và sanitized stack; backend không
  cần được khởi động để build.
- Cách khắc phục: giữ build độc lập backend; sửa typed client/build-safe error
  state. Không khởi động FastAPI để ép build pass.
- Kết quả mong đợi: production build pass và liệt kê đủ route.
- Log được phép chia sẻ: route, module, error type và stack đã sanitize.
- Dữ liệu không được chia sẻ: `.next` archive, `.env.local`, API response thật.
- Ngày cập nhật: 2026-07-24.

## WEB-PORT-001 — Frontend port bị chiếm

- Triệu chứng: Next.js không bind được port 3000.
- Nguyên nhân có thể: một frontend/process khác đang listen.
- Cách kiểm tra:
  `Get-NetTCPConnection -State Listen -LocalPort 3000 | Select LocalAddress,LocalPort,OwningProcess`.
- Cách khắc phục: Project Owner xác định đúng PID/process; dừng đúng process hoặc
  chọn port loopback khác. Không kill hàng loạt.
- Kết quả mong đợi: port 3000 free hoặc frontend chạy trên port mới đã ghi rõ.
- Log được phép chia sẻ: port, PID, process name.
- Dữ liệu không được chia sẻ: full process/environment dump.
- Ngày cập nhật: 2026-07-24.

## WEB-PORT-002 — Backend port bị chiếm

- Triệu chứng: uvicorn không bind được port 8000.
- Nguyên nhân có thể: backend/process khác đang listen.
- Cách kiểm tra:
  `Get-NetTCPConnection -State Listen -LocalPort 8000 | Select LocalAddress,LocalPort,OwningProcess`.
- Cách khắc phục: Project Owner xác nhận PID rồi dừng đúng process hoặc đổi port
  loopback và cập nhật health URL.
- Kết quả mong đợi: FastAPI listen duy nhất trên địa chỉ/port đã chọn.
- Log được phép chia sẻ: port, PID, process name.
- Dữ liệu không được chia sẻ: environment dump hoặc request payload.
- Ngày cập nhật: 2026-07-24.

## WEB-API-001 — Frontend không gọi được API

- Triệu chứng: schema panel hiển thị “Chưa kết nối được API schema”.
- Nguyên nhân có thể: backend chưa chạy; `WEB_API_ORIGIN` sai port/không hợp lệ;
  Next rewrite chưa hoạt động.
- Cách kiểm tra: Project Owner gọi trực tiếp
  `Invoke-RestMethod http://127.0.0.1:8000/api/v1/system/health`, rồi gọi
  `Invoke-RestMethod http://127.0.0.1:3000/api/v1/system/health`; kiểm tra browser
  network path nhưng không chia sẻ response thật.
- Cách khắc phục: xác nhận direct backend health trước, đặt
  `WEB_API_ORIGIN=http://127.0.0.1:8000` trước khi start Next rồi thử proxied
  health. Không bật wildcard CORS hoặc bind `0.0.0.0`.
- Kết quả mong đợi: direct và proxied health cùng pass; khi backend dừng, UI giữ
  controlled error state.
- Log được phép chia sẻ: HTTP method, sanitized URL path, status code.
- Dữ liệu không được chia sẻ: response body nghiệp vụ, headers có token.
- Ngày cập nhật: 2026-07-24.

## WEB-CORS-001 — CORS bị chặn

- Triệu chứng: browser console báo cross-origin request blocked.
- Nguyên nhân có thể: client đã bị cấu hình sai thành absolute backend URL thay
  vì same-origin `/api/v1`, nên bỏ qua Next rewrite.
- Cách kiểm tra: ghi frontend origin, backend origin và browser CORS error đã
  sanitize.
- Cách khắc phục: phục hồi `NEXT_PUBLIC_API_BASE_URL=/api/v1` và
  `WEB_API_ORIGIN=http://127.0.0.1:8000`; không dùng `allow_origins=["*"]`.
- Kết quả mong đợi: browser gọi same-origin Next route, không cần CORS; Phase 0.6
  vẫn loopback-only.
- Log được phép chia sẻ: origins, status code, tên header không có value nhạy cảm.
- Dữ liệu không được chia sẻ: cookies, authorization header, request payload.
- Ngày cập nhật: 2026-07-24.

## WEB-DB-001 — Không kết nối được PostgreSQL

- Triệu chứng: connection refused, timeout hoặc container unhealthy.
- Nguyên nhân có thể: Docker Desktop chưa sẵn sàng, container chưa healthy, port
  55432 bị chiếm hoặc URL sai.
- Cách kiểm tra: Project Owner chạy compose `ps` và `pg_isready` theo
  `OPERATIONS_RUNBOOK.md`.
- Cách khắc phục: xác nhận Docker engine, loopback port và synthetic database
  name; không đổi schema bằng tay.
- Kết quả mong đợi: `pg_isready` báo accepting connections.
- Log được phép chia sẻ: container state, error code, tối đa 100 dòng sanitized.
- Dữ liệu không được chia sẻ: password, `DATABASE_URL`, real table rows.
- Ngày cập nhật: 2026-07-24.

## WEB-MIGRATION-001 — Alembic migration thất bại

- Triệu chứng: `alembic upgrade head` trả traceback hoặc revision mismatch.
- Nguyên nhân có thể: DB chưa sẵn sàng, URL sai, schema permission hoặc migration
  history lệch.
- Cách kiểm tra: `alembic heads`, `alembic current`; ghi revision IDs và exception
  type.
- Cách khắc phục: dừng; không tự drop/alter production-like data. Với database
  synthetic mới, Project Owner quyết định recreate theo runbook sau khi review.
- Kết quả mong đợi: current `0002_phase0_tables (head)`.
- Log được phép chia sẻ: revision ID, exception type, sanitized SQL object name.
- Dữ liệu không được chia sẻ: connection string, row data, real identifiers.
- Ngày cập nhật: 2026-07-24.

## WEB-ENV-001 — Thiếu environment variable

- Triệu chứng: service báo thiếu `DATABASE_URL` hoặc API base URL sai.
- Nguyên nhân có thể: biến chưa set trong đúng PowerShell hoặc dùng tên không
  được Next.js expose.
- Cách kiểm tra: chỉ kiểm tra biến có tồn tại, không in giá trị secret.
- Cách khắc phục: set biến trong đúng cửa sổ theo runbook; giữ file commit chỉ là
  `.env.web.example`.
- Kết quả mong đợi: service nhận config, không có `.env.local` được track.
- Log được phép chia sẻ: tên biến thiếu, không chia sẻ value.
- Dữ liệu không được chia sẻ: secret, credential, connection URL.
- Ngày cập nhật: 2026-07-24.

## WEB-NETWORK-001 — Không truy cập được từ máy khác

- Triệu chứng: máy khác trong LAN không mở được frontend/backend.
- Nguyên nhân có thể: đúng thiết kế Phase 0.6 đang bind `127.0.0.1`.
- Cách kiểm tra: xác nhận listener LocalAddress là loopback.
- Cách khắc phục: không mở firewall hoặc đổi sang `0.0.0.0` trong Phase 0.6.
  Tạo task network deployment riêng sau security review.
- Kết quả mong đợi: chỉ máy local truy cập được.
- Log được phép chia sẻ: local address và port.
- Dữ liệu không được chia sẻ: network topology, public IP, firewall export.
- Ngày cập nhật: 2026-07-24.

## WEB-UI-001 — Bố cục hoặc tiếng Việt hiển thị sai

- Triệu chứng: chữ có dấu bị cắt, font thay đổi bất thường, H1/action chồng nhau
  hoặc trang có horizontal overflow ngoài bảng.
- Nguyên nhân có thể: browser zoom/viewport, font hệ thống thiếu, cache build cũ
  hoặc CSS regression.
- Cách kiểm tra: ghi route, viewport, zoom và screenshot không có dữ liệu thật;
  đối chiếu `VISUAL_QA_CHECKLIST.md`.
- Cách khắc phục: dừng visual QA tại route lỗi, xác nhận system font stack và
  rebuild frontend. Không thêm remote font/CDN để che lỗi.
- Kết quả mong đợi: dấu tiếng Việt đầy đủ, không overflow ngoài vùng bảng, focus
  và action không chồng nhau.
- Log được phép chia sẻ: route, viewport, zoom, screenshot minh họa.
- Dữ liệu không được chia sẻ: hồ sơ, PDF/ảnh thật, response nghiệp vụ hoặc user
  path.
- Ngày cập nhật: 2026-07-28.

## WEB-UI-002 — Navigation hoặc badge không đúng Phase 0.8

- Triệu chứng: sidebar có 11 mục, xuất hiện “Kiểm tra OCR”, có nhiều badge thử
  nghiệm hoặc top bar còn environment/role placeholder cũ.
- Nguyên nhân có thể: process frontend dùng build/cache cũ hoặc source khác
  worktree.
- Cách kiểm tra: xác nhận branch `demo-web-platform`, dừng frontend, kiểm đúng
  repo root và chạy lại finite build.
- Cách khắc phục: không sửa route tạm trong browser; khởi động lại từ đúng
  worktree sau khi frontend gate pass.
- Kết quả mong đợi: đúng 10 mục, một `Bản thử nghiệm`, không có mục OCR hoặc
  environment/role copy cũ.
- Log được phép chia sẻ: branch, HEAD, route và screenshot minh họa.
- Dữ liệu không được chia sẻ: full environment, credential hoặc dữ liệu thật.
- Ngày cập nhật: 2026-07-28.
