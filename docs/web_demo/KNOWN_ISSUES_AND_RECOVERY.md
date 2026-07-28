# Known issues và recovery cho web demo local

Tài liệu này chỉ áp dụng cho dữ liệu synthetic và runtime local do Project Owner trực
tiếp vận hành. Log được phép chia sẻ chỉ gồm error code, timestamp, exit code, version,
PID/port và tối đa 100 dòng technical log đã loại credential/path cá nhân. Tuyệt đối
không gửi OCR text, tên người, địa chỉ, CCCD/CMND, tên file nhạy cảm hoặc dữ liệu vụ án.

## WEB-NODE-PATH-001

- Ngày ghi nhận: 2026-07-28.
- Môi trường: Windows PowerShell, system Node/npm.
- Triệu chứng: `node` hoặc `npm.cmd` không được nhận diện dù Node đã cài.
- Nguyên nhân gốc: `PATH` của phiên PowerShell cũ chưa có thư mục Node system.
- Cách kiểm tra: chạy `Get-Command node`, `Get-Command npm.cmd`, rồi
  `scripts\web_demo\check_prerequisites.ps1`.
- Cách khắc phục: đóng/mở lại PowerShell sau khi cài Node; dùng system Node, không dùng
  runtime bundled hoặc copy binary vào repo.
- Phòng ngừa: kiểm tra prerequisite trước `npm.cmd ci`.
- Kết quả mong đợi: helper in `[OK] node` và `[OK] npm`.
- Log được phép: version và path đã thay phần user bằng `<REDACTED>`.
- Dữ liệu cấm: token npm, credential registry, path cá nhân nguyên dạng.
- Trạng thái: Đã có recovery.

## WEB-NPM-LOCK-001

- Ngày ghi nhận: 2026-07-28.
- Môi trường: `apps/web`, npm 11, lockfile v3.
- Triệu chứng: thiếu `node_modules`, `npm.cmd ci` lỗi, hoặc lockfile lệch `package.json`.
- Nguyên nhân gốc: dependency chưa được cài từ lockfile canonical.
- Cách kiểm tra: xác nhận `package-lock.json` tồn tại và chạy `npm.cmd ci`.
- Cách khắc phục: Project Owner chạy
  `scripts\web_demo\start_local.ps1 -InstallDependencies`; không tạo lockfile thủ công.
- Phòng ngừa: dùng `npm.cmd ci`, không dùng install tùy ý trong local run.
- Kết quả mong đợi: install kết thúc exit `0`, audit sạch.
- Log được phép: package name công khai, advisory ID, exit code.
- Dữ liệu cấm: registry token, `.npmrc` riêng, path cá nhân.
- Trạng thái: Đã có recovery.

## WEB-ALEMBIC-IMPORT-001

- Ngày ghi nhận: 2026-07-28.
- Môi trường: Python venv và Alembic tại repo root.
- Triệu chứng: `No module named court_ocr_extract` hoặc Alembic không tìm model.
- Nguyên nhân gốc: dùng sai Python, sai working directory hoặc web dependencies thiếu.
- Cách kiểm tra: từ `<REPO_ROOT>` chạy
  `.venv\Scripts\python.exe -m alembic current`.
- Cách khắc phục: trở lại repo root, dùng đúng `.venv`; cài dependency theo
  `requirements-web.txt` nếu môi trường chưa hoàn chỉnh.
- Phòng ngừa: không gọi Python system và không chạy migration từ `apps/web`.
- Kết quả mong đợi: revision `0002_phase0_tables (head)`.
- Log được phép: sanitized import traceback và revision.
- Dữ liệu cấm: `DATABASE_URL` đầy đủ ngoài credential synthetic local.
- Trạng thái: Đã có recovery.

## WEB-PS-LAUNCHER-001

- Ngày ghi nhận: 2026-07-28.
- Môi trường: Windows PowerShell 5.1.
- Triệu chứng: launcher báo parse error hoặc service thoát ngay.
- Nguyên nhân gốc: command nhiều dòng làm `--host`/`--port` thành statement riêng, hoặc
  execution policy chặn file.
- Cách kiểm tra: chạy test AST trong `tests/web/frontend/test_phase09_operations_contract.py`.
- Cách khắc phục: gọi
  `powershell -ExecutionPolicy Bypass -File scripts\web_demo\start_local.ps1`; không
  dựng launcher tạm bằng here-string.
- Phòng ngừa: giữ command backend/frontend trên đúng một statement.
- Kết quả mong đợi: launcher ghi state ngoài Git và hai loopback port sẵn sàng.
- Log được phép: parser error, script name, line/column.
- Dữ liệu cấm: nội dung environment secret.
- Trạng thái: Đã có recovery.

## WEB-NEXT-SWC-LOCK-001

- Ngày ghi nhận: 2026-07-28.
- Môi trường: Next.js local build/dev.
- Triệu chứng: build hoặc cleanup báo file trong `.next` đang bị process giữ.
- Nguyên nhân gốc: frontend dev process cũ vẫn chạy.
- Cách kiểm tra: chạy `status_local.ps1` và kiểm tra listener 3000/PID.
- Cách khắc phục: chạy `stop_local.ps1`; chỉ xóa `apps/web/.next` khi port 3000 không
  còn listener và runtime state xác nhận frontend đã dừng.
- Phòng ngừa: luôn stop bằng state trước build.
- Kết quả mong đợi: `.next` có thể tái tạo bằng build tiếp theo.
- Log được phép: PID, port, tên artifact `.next`.
- Dữ liệu cấm: broad process listing hoặc thông tin workload khác.
- Trạng thái: Đã có recovery.

## WEB-DOCKER-STATE-001

- Ngày ghi nhận: 2026-07-28.
- Môi trường: Docker Desktop và compose PostgreSQL synthetic.
- Triệu chứng: engine không sẵn sàng, container unhealthy hoặc compose state cũ.
- Nguyên nhân gốc: Docker Desktop chưa chạy hoặc lần local run trước dừng không hoàn chỉnh.
- Cách kiểm tra: `docker compose -f ops\web_demo\docker-compose.postgres.yml ps`.
- Cách khắc phục: Project Owner khởi động Docker Desktop; chạy `stop_local.ps1`, sau đó
  start lại. Không xóa volume khi chưa có quyết định.
- Phòng ngừa: stop local trước khi power off.
- Kết quả mong đợi: PostgreSQL `healthy` trên loopback port 55432.
- Log được phép: tối đa 100 dòng compose/PostgreSQL synthetic log.
- Dữ liệu cấm: database thật, dump, record nghiệp vụ.
- Trạng thái: Đã có recovery.

## WEB-PORT-001

- Ngày ghi nhận: 2026-07-28.
- Môi trường: loopback ports 3000, 8000, 55432.
- Triệu chứng: port in use, listener không sẵn sàng hoặc state stale.
- Nguyên nhân gốc: runtime cũ hoặc ứng dụng khác đang sở hữu port.
- Cách kiểm tra: `status_local.ps1` và `Get-NetTCPConnection -State Listen`.
- Cách khắc phục: nếu PID thuộc state web demo thì chạy `stop_local.ps1`; nếu không,
  dừng và để Project Owner quyết định, không kill theo tên.
- Phòng ngừa: prerequisite/status trước start.
- Kết quả mong đợi: listener đúng PID trên `127.0.0.1`.
- Log được phép: port, exact PID, trạng thái listener.
- Dữ liệu cấm: danh sách toàn bộ process của máy.
- Trạng thái: Đã có recovery.

## WEB-AUDIT-001

- Ngày ghi nhận: 2026-07-28.
- Môi trường: npm dependency security gate.
- Triệu chứng: `npm.cmd audit` hoặc `npm.cmd audit --omit=dev` trả khác `0`.
- Nguyên nhân gốc: dependency tree có advisory mới hoặc lockfile drift.
- Cách kiểm tra: chạy hai audit command trong `apps/web`.
- Cách khắc phục: dừng local start, ghi advisory ID và mở task hardening riêng; không
  tự chạy audit fix.
- Phòng ngừa: audit sau `npm.cmd ci`, exact pin và review lockfile.
- Kết quả mong đợi: `found 0 vulnerabilities`.
- Log được phép: package công khai, severity, advisory ID.
- Dữ liệu cấm: npm token và cấu hình registry riêng.
- Trạng thái: Fail-closed.

## WEB-API-PROXY-001

- Ngày ghi nhận: 2026-07-28.
- Môi trường: Next same-origin proxy `/api/v1`.
- Triệu chứng: frontend trả 404/502 trong khi direct backend health có thể hoạt động.
- Nguyên nhân gốc: backend chưa sẵn sàng hoặc `WEB_API_ORIGIN` sai exact loopback origin.
- Cách kiểm tra: so sánh health ở ports 8000 và 3000.
- Cách khắc phục: xác nhận backend trước; giữ
  `WEB_API_ORIGIN=http://127.0.0.1:8000`; không bật wildcard CORS.
- Phòng ngừa: dùng `run_frontend.ps1` canonical.
- Kết quả mong đợi: hai health request cùng trả `status=ok`.
- Log được phép: HTTP status, route, sanitized Next error.
- Dữ liệu cấm: response nghiệp vụ hoặc header chứa credential.
- Trạng thái: Đã có recovery.

## WEB-POWER-OFF-001

- Ngày ghi nhận: 2026-07-28.
- Môi trường: Windows shutdown/restart khi local demo đang chạy.
- Triệu chứng: lần start sau có stale state, compose container hoặc `.next` lock.
- Nguyên nhân gốc: máy tắt trước khi launcher hoàn tất stop.
- Cách kiểm tra: chạy `status_local.ps1`, compose `ps` và kiểm tra ba port local.
- Cách khắc phục: chạy `stop_local.ps1`; nếu state stale, chỉ xử lý exact PID/compose
  được nhận diện, không broad kill.
- Phòng ngừa: stop local trước khi sleep/restart/power off.
- Kết quả mong đợi: state được xóa, ports được giải phóng, compose down.
- Log được phép: state timestamp, exact PID/port và compose status.
- Dữ liệu cấm: full machine inventory hoặc log ứng dụng khác.
- Trạng thái: Đã có recovery.
