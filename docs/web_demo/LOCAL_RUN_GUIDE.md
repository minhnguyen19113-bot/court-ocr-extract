# Hướng dẫn chạy web demo local

Chỉ Project Owner chạy các lệnh runtime dưới đây. Dùng dữ liệu synthetic, giữ bind
`127.0.0.1`, không mở firewall/browser tự động và không dùng dữ liệu thật. Thay
`<REPO_ROOT>` bằng worktree web local.

## Luồng một lệnh

Từ `<REPO_ROOT>`:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\web_demo\start_local.ps1 -InstallDependencies
powershell -ExecutionPolicy Bypass -File scripts\web_demo\status_local.ps1
powershell -ExecutionPolicy Bypass -File scripts\web_demo\stop_local.ps1
```

Lần sau có thể bỏ `-InstallDependencies`. Dùng `-SkipDatabase` khi PostgreSQL synthetic
đã do Project Owner quản lý riêng; dùng `-SkipMigration` chỉ khi revision đã được xác
nhận. Start fail-fast và dọn đúng service do chính lần gọi đó tạo. State/log nằm trong
`%LOCALAPPDATA%\court-ocr-extract\web-demo`, không nằm trong Git.

Kết quả mong đợi: dashboard ở `http://127.0.0.1:3000/dashboard`; status báo frontend
3000 và backend 8000 có đúng PID; stop giải phóng runtime. Nếu lỗi, tra
`KNOWN_ISSUES_AND_RECOVERY.md`.

## Luồng thủ công 14 bước

1. Tại `<REPO_ROOT>`, chạy
   `powershell -ExecutionPolicy Bypass -File scripts\web_demo\check_prerequisites.ps1`.
   Mong đợi các prerequisite `[OK]`; nếu lỗi xem `WEB-NODE-PATH-001` hoặc
   `WEB-NPM-LOCK-001`. Script tự kết thúc.
2. Project Owner mở Docker Desktop. Mong đợi engine ready; nếu lỗi xem
   `WEB-DOCKER-STATE-001`. Dừng bằng Docker Desktop sau khi compose đã down.
3. Chạy
   `docker compose -f ops\web_demo\docker-compose.postgres.yml up -d`.
   Mong đợi PostgreSQL chỉ bind 55432 loopback; dừng bằng cùng compose file với `down`.
4. Chạy
   `docker compose -f ops\web_demo\docker-compose.postgres.yml exec postgres pg_isready -U web_demo_synthetic -d court_ocr_web_synthetic`.
   Mong đợi accepting connections; nếu lỗi xem `WEB-DOCKER-STATE-001`.
5. Đặt synthetic `DATABASE_URL` theo `.env.web.example`, rồi chạy
   `.venv\Scripts\python.exe -m alembic upgrade head`. Mong đợi exit `0`; nếu lỗi xem
   `WEB-ALEMBIC-IMPORT-001`.
6. Chạy `.venv\Scripts\python.exe -m alembic current`. Mong đợi
   `0002_phase0_tables (head)`. Command tự kết thúc.
7. Trong PowerShell backend tại `<REPO_ROOT>`, chạy
   `powershell -ExecutionPolicy Bypass -File scripts\web_demo\run_backend.ps1`.
   Mong đợi port 8000; lỗi xem `WEB-PS-LAUNCHER-001`/`WEB-PORT-001`; dừng `Ctrl+C`.
8. Từ cửa sổ khác, chạy
   `Invoke-RestMethod http://127.0.0.1:8000/api/v1/system/health`.
   Mong đợi `status=ok`; request tự kết thúc.
9. Tại `<REPO_ROOT>\apps\web`, chạy `npm.cmd ci`, `npm.cmd audit`, rồi
   `npm.cmd audit --omit=dev`. Mong đợi exit `0`; lỗi xem `WEB-AUDIT-001`.
10. Tại `<REPO_ROOT>`, chạy
    `powershell -ExecutionPolicy Bypass -File scripts\web_demo\run_frontend.ps1`.
    Mong đợi port 3000; lỗi xem `WEB-NEXT-SWC-LOCK-001`/`WEB-PORT-001`; dừng `Ctrl+C`.
11. Chạy
    `Invoke-RestMethod http://127.0.0.1:3000/api/v1/system/health`.
    Mong đợi `status=ok`; nếu 404/502 xem `WEB-API-PROXY-001`.
12. Project Owner tự mở `http://127.0.0.1:3000/dashboard` và thực hiện
    `VISUAL_QA_CHECKLIST.md`. Đóng tab khi xong; không gửi dữ liệu thật.
13. Nhấn `Ctrl+C` ở frontend rồi backend. Nếu listener còn tồn tại, không broad kill;
    tra exact PID theo `WEB-PORT-001`.
14. Chạy
    `docker compose -f ops\web_demo\docker-compose.postgres.yml down`.
    Mong đợi compose dừng nhưng dữ liệu bind local giữ nguyên. Trước power off, xác nhận
    ba port đã giải phóng; nếu chưa xem `WEB-POWER-OFF-001`.
