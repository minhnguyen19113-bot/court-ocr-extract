# Runbook vận hành local dành cho Project Owner

> Phase 0.9: luồng start/status/stop ngắn và bản thủ công 14 bước nằm tại
> `LOCAL_RUN_GUIDE.md`; known-error canonical nằm tại
> `KNOWN_ISSUES_AND_RECOVERY.md`. Chỉ Project Owner gọi các script runtime.

## 1. Phạm vi và trách nhiệm

Runbook này mô tả từng thao tác riêng. Project Owner trực tiếp chạy service,
mở browser và dừng service. Codex không chạy các lệnh vận hành trong tài liệu
này. Thay `<REPO_ROOT>` bằng thư mục worktree web local.

Không dùng PDF, ảnh, OCR text, Excel hoặc thông tin vụ án thật trong lần chạy
đầu. Không bind `0.0.0.0` và không mở Windows Firewall.

## 2. Trình tự chạy lần đầu

### Bước 1 — Kiểm tra prerequisite

- Thư mục hiện tại: `<REPO_ROOT>`.
- Lệnh:

  ```powershell
  powershell -ExecutionPolicy Bypass -File scripts\web_demo\check_prerequisites.ps1
  ```

- Kết quả mong đợi: thấy path system của `node`, `npm`, Python venv; có
  `package-lock.json`, `.env.web.example`; các port 3000, 8000, 55432 được báo
  `FREE`.
- Dấu hiệu lỗi: `[MISSING]` hoặc `[IN USE]`.
- Bước tiếp theo: xử lý đúng mã lỗi trong `TROUBLESHOOTING.md`, rồi chạy lại.
- Lệnh dừng: script tự kết thúc, không có process cần dừng.

### Bước 2 — Mở PowerShell số 1 cho database

- Thư mục hiện tại: `<REPO_ROOT>`.
- Thao tác: mở một cửa sổ PowerShell mới và chạy `Set-Location <REPO_ROOT>`.
- Kết quả mong đợi: prompt đang ở đúng worktree `demo-web-platform`.
- Dấu hiệu lỗi: `git branch --show-current` không trả `demo-web-platform`.
- Bước tiếp theo: dừng; không tự switch branch hoặc dùng worktree khác.
- Lệnh dừng: `exit` nếu chưa khởi động database.

### Bước 3 — Project Owner tự khởi động database

- Thư mục hiện tại: `<REPO_ROOT>`.
- Thao tác/lệnh:

  1. Project Owner tự mở Docker Desktop và chờ engine báo sẵn sàng.
  2. Chạy:

     ```powershell
     docker compose -f ops\web_demo\docker-compose.postgres.yml up -d
     ```

- Kết quả mong đợi: service `postgres` được tạo, chỉ bind
  `127.0.0.1:55432`.
- Dấu hiệu lỗi: không kết nối Docker engine, image pull lỗi hoặc port bị chiếm.
- Bước tiếp theo: xem `WEB-DB-001` hoặc lỗi port trong troubleshooting.
- Lệnh dừng:

  ```powershell
  docker compose -f ops\web_demo\docker-compose.postgres.yml down
  ```

### Bước 4 — Kiểm tra database sẵn sàng

- Thư mục hiện tại: `<REPO_ROOT>`.
- Lệnh:

  ```powershell
  docker compose -f ops\web_demo\docker-compose.postgres.yml ps
  docker compose -f ops\web_demo\docker-compose.postgres.yml exec postgres pg_isready -U web_demo_synthetic -d court_ocr_web_synthetic
  ```

- Kết quả mong đợi: container `healthy`; `pg_isready` báo accepting connections.
- Dấu hiệu lỗi: trạng thái `starting`, `unhealthy`, `exited` hoặc connection
  rejected.
- Bước tiếp theo: chờ healthcheck hữu hạn; nếu vẫn lỗi, xem tối đa 100 dòng log
  synthetic theo Bước 16.
- Lệnh dừng: dùng lệnh `down` ở Bước 3.

### Bước 5 — Chạy Alembic migration

- Thư mục hiện tại: `<REPO_ROOT>`.
- Lệnh:

  ```powershell
  $env:DATABASE_URL="postgresql+psycopg://web_demo_synthetic:local_development_only@127.0.0.1:55432/court_ocr_web_synthetic"
  .venv\Scripts\python.exe -m alembic upgrade head
  .venv\Scripts\python.exe -m alembic current
  ```

- Kết quả mong đợi: current revision là `0002_phase0_tables (head)`.
- Dấu hiệu lỗi: connection refused, authentication error hoặc migration
  traceback.
- Bước tiếp theo: xem `WEB-MIGRATION-001`; không tự sửa bảng/schema bằng tay.
- Lệnh dừng: migration tự kết thúc; database dừng ở Bước 15.

### Bước 6 — Mở PowerShell số 2 cho FastAPI

- Thư mục hiện tại: `<REPO_ROOT>`.
- Thao tác: mở PowerShell mới, `Set-Location <REPO_ROOT>`.
- Kết quả mong đợi: Python venv tồn tại.
- Dấu hiệu lỗi: thiếu `.venv\Scripts\python.exe`.
- Bước tiếp theo: hoàn thiện Python prerequisite; không dùng Python system khác
  không rõ dependency.
- Lệnh dừng: `exit` nếu backend chưa chạy.

### Bước 7 — Project Owner tự chạy backend

- Thư mục hiện tại: `<REPO_ROOT>`.
- Lệnh:

  ```powershell
  $env:DATABASE_URL="postgresql+psycopg://web_demo_synthetic:local_development_only@127.0.0.1:55432/court_ocr_web_synthetic"
  .venv\Scripts\python.exe -m uvicorn court_ocr_extract.web_api.app:app --host 127.0.0.1 --port 8000
  ```

- Kết quả mong đợi: FastAPI lắng nghe tại `http://127.0.0.1:8000`.
- Dấu hiệu lỗi: import error, port conflict hoặc process thoát.
- Bước tiếp theo: xem `WEB-PORT-002`, `WEB-ENV-001` hoặc sanitized traceback.
- Lệnh dừng: nhấn `Ctrl+C` trong PowerShell số 2.

### Bước 8 — Kiểm tra health endpoint

- Thư mục hiện tại: một PowerShell không chạy foreground service.
- Lệnh:

  ```powershell
  Invoke-RestMethod http://127.0.0.1:8000/api/v1/system/health
  Invoke-RestMethod http://127.0.0.1:8000/api/v1/system/schema
  Invoke-RestMethod http://127.0.0.1:8000/api/v1/forms/capabilities
  ```

- Kết quả mong đợi: health `status=ok`; schema có 14 cột; form capability không
  có format `AVAILABLE`.
- Dấu hiệu lỗi: connection refused, HTTP error hoặc contract sai.
- Bước tiếp theo: dừng local run nếu contract sai; không mở mutation.
- Lệnh dừng: các request tự kết thúc.

### Bước 9 — Mở PowerShell số 3 cho frontend

- Thư mục hiện tại: `<REPO_ROOT>\apps\web`.
- Thao tác: mở PowerShell mới và chạy
  `Set-Location <REPO_ROOT>\apps\web`.
- Kết quả mong đợi: `package.json` và `package-lock.json` tồn tại.
- Dấu hiệu lỗi: sai thư mục hoặc thiếu lockfile.
- Bước tiếp theo: xem `WEB-LOCK-001`.
- Lệnh dừng: `exit` nếu frontend chưa chạy.

Trước khi mở frontend, Project Owner chạy finite security gate:

```powershell
npm ci
npm audit
npm audit --omit=dev
```

Kết quả mong đợi Phase 0.7 là cả hai audit trả exit `0` và
`found 0 vulnerabilities`. Nếu khác, không chạy dev server; xem `WEB-AUDIT-001`.

### Bước 10 — Project Owner tự chạy frontend

- Thư mục hiện tại: `<REPO_ROOT>\apps\web`.
- Lệnh:

  ```powershell
  $env:WEB_API_ORIGIN="http://127.0.0.1:8000"
  $env:NEXT_PUBLIC_API_BASE_URL="/api/v1"
  npm run dev -- --hostname 127.0.0.1 --port 3000
  ```

- Kết quả mong đợi: Next.js lắng nghe tại `http://127.0.0.1:3000`.
- Dấu hiệu lỗi: Node/npm không nhận diện, dependency lỗi, build error hoặc port
  conflict.
- Bước tiếp theo: xem `WEB-NODE-001`, `WEB-NPM-001`, `WEB-INSTALL-001` hoặc
  `WEB-PORT-001`.
- Lệnh dừng: nhấn `Ctrl+C` trong PowerShell số 3.

`next.config.mjs` rewrite same-origin `/api/v1/:path*` tới loopback backend
`${WEB_API_ORIGIN}/api/v1/:path*`. Browser không gọi cross-origin nên FastAPI
không bật CORS. Phase 0.7 fail-closed nếu `WEB_API_ORIGIN` không có dạng exact
`http://127.0.0.1:<port>`; không bind rộng hoặc bật wildcard CORS.

### Bước 10a — Project Owner kiểm tra health qua frontend proxy

- Thư mục hiện tại: PowerShell bất kỳ, sau khi backend và frontend đều đang chạy.
- Lệnh:

  ```powershell
  Invoke-RestMethod http://127.0.0.1:3000/api/v1/system/health
  ```

- Kết quả mong đợi: cùng contract `status=ok` như direct backend health.
- Dấu hiệu lỗi: HTTP 404/502, connection refused hoặc controlled unavailable state.
- Bước tiếp theo: xác nhận direct health trước, sau đó kiểm tra `WEB_API_ORIGIN`;
  xem `WEB-API-001`. Không bật CORS để che lỗi rewrite.
- Lệnh dừng: request tự kết thúc.

### Bước 11 — Project Owner mở browser

- Thư mục hiện tại: không áp dụng.
- URL: `http://127.0.0.1:3000/dashboard`.
- Kết quả mong đợi: application shell có một badge `Bản thử nghiệm`, sidebar 10
  mục và dashboard bốn summary card với một note `Dữ liệu minh họa`.
- Dấu hiệu lỗi: browser không kết nối hoặc trang Next error.
- Bước tiếp theo: kiểm tra PowerShell số 3 và `WEB-BUILD-001`.
- Lệnh dừng: đóng tab/browser; không ảnh hưởng service.

### Bước 12 — Kiểm tra dashboard và routes

- Thư mục hiện tại: browser do Project Owner điều khiển.
- Route checklist:

  ```text
  /dashboard
  /intake
  /jobs
  /jobs/synthetic-job
  /review
  /review/synthetic-review
  /publishing
  /exports
  /forms
  /forms/synthetic-form
  /audit
  /admin
  /help
  ```

- Kết quả mong đợi: đủ 13 route không 404; 10 sidebar items mở được; không có
  mục `Kiểm tra OCR`; status không chỉ dùng màu; các action chưa khả dụng bị vô
  hiệu; chỉ có dữ liệu minh họa.
- Dấu hiệu lỗi: missing route, hydration error, active generation control hoặc
  dữ liệu không synthetic.
- Bước tiếp theo: dừng run và ghi route + sanitized browser error; không chia sẻ
  tài liệu/nghiệp vụ thật.
- Lệnh dừng: không có; tiếp tục Bước 13.

### Bước 13 — Dừng frontend

- Thư mục hiện tại: PowerShell số 3.
- Lệnh/thao tác: `Ctrl+C`, xác nhận terminate nếu PowerShell hỏi.
- Kết quả mong đợi: process Next.js kết thúc, port 3000 không còn listen.
- Dấu hiệu lỗi: process vẫn giữ port.
- Bước tiếp theo: xác định PID theo `PORTS_AND_NETWORK.md`; không dùng kill hàng
  loạt.
- Lệnh dừng bổ sung: không có lệnh tự động trong runbook.

### Bước 14 — Dừng backend

- Thư mục hiện tại: PowerShell số 2.
- Lệnh/thao tác: `Ctrl+C`.
- Kết quả mong đợi: uvicorn kết thúc, port 8000 không còn listen.
- Dấu hiệu lỗi: process vẫn giữ port.
- Bước tiếp theo: xác định đúng PID; không dừng process không thuộc demo.
- Lệnh dừng bổ sung: không có lệnh tự động trong runbook.

### Bước 15 — Project Owner tự dừng database

- Thư mục hiện tại: `<REPO_ROOT>` trong PowerShell số 1.
- Lệnh:

  ```powershell
  docker compose -f ops\web_demo\docker-compose.postgres.yml down
  ```

- Kết quả mong đợi: container và compose network được dừng/xóa; bind data local
  vẫn giữ cho lần chạy sau.
- Dấu hiệu lỗi: Docker engine không phản hồi.
- Bước tiếp theo: Project Owner kiểm tra Docker Desktop; không xóa data directory
  khi chưa quyết định.
- Lệnh dừng: Project Owner tự đóng Docker Desktop nếu không còn workload khác.

### Bước 16 — Xem log an toàn

- Thư mục hiện tại: `<REPO_ROOT>`.
- Lệnh:

  ```powershell
  docker compose -f ops\web_demo\docker-compose.postgres.yml logs --tail 100 postgres
  ```

- Kết quả mong đợi: chỉ log kỹ thuật của database synthetic.
- Dấu hiệu lỗi: log chứa credential, user path hoặc dữ liệu nghiệp vụ.
- Bước tiếp theo: không chia sẻ phần nhạy cảm; chỉ gửi error code, timestamp và
  sanitized stack/log tail.
- Lệnh dừng: command tự kết thúc; không dùng follow mode.

### Bước 17 — Xử lý restart

- Thư mục hiện tại: theo từng cửa sổ ở trên.
- Trình tự: dừng frontend → dừng backend → dừng database; sau đó khởi động lại
  database → migration → backend → health → frontend.
- Kết quả mong đợi: không còn process cũ giữ port, migration idempotent tại head.
- Dấu hiệu lỗi: duplicate listener, stale process hoặc migration revision lệch.
- Bước tiếp theo: dừng tại component lỗi; không restart toàn hệ thống bằng script
  ẩn.
- Lệnh dừng: dùng đúng lệnh/thao tác tại Bước 13–15.

## PROJECT OWNER FIRST LOCAL RUN CHECKLIST

- [ ] System Node và npm đáp ứng contract.
- [ ] Python venv hoạt động.
- [ ] Python web dependencies đã cài.
- [ ] `apps/web/package-lock.json` tồn tại và đã review.
- [ ] `npm ci` pass.
- [ ] PostgreSQL do Project Owner khởi động và chỉ bind loopback.
- [ ] Alembic migration đạt `0002_phase0_tables (head)`.
- [ ] Backend do Project Owner khởi động trên `127.0.0.1:8000`.
- [ ] `/api/v1/system/health` trả `status=ok`.
- [ ] Frontend do Project Owner khởi động trên `127.0.0.1:3000`.
- [ ] `http://127.0.0.1:3000/api/v1/system/health` trả `status=ok` qua rewrite.
- [ ] Dashboard mở được.
- [ ] 10 sidebar items mở được.
- [ ] 13 business routes không 404/runtime error.
- [ ] Schema endpoint trả đúng 14 cột.
- [ ] Forms capability hiển thị generation chưa triển khai.
- [ ] Không dùng dữ liệu thật.
- [ ] Không bind public address hoặc mở firewall.
- [ ] Đã biết dừng frontend bằng `Ctrl+C`.
- [ ] Đã biết dừng backend bằng `Ctrl+C`.
- [ ] Đã biết dừng database bằng `docker compose ... down`.

## PROJECT OWNER PHASE 0.8 VISUAL QA

Sau khi Bước 12 đạt, thực hiện checklist tại
`docs/web_demo/VISUAL_QA_CHECKLIST.md`:

1. Kiểm viewport `1440×900`, `1280×800`, `1024×768`, `768×1024`,
   `390×844` và zoom `200%`.
2. Chụp dashboard desktop/tablet/mobile.
3. Chụp đủ 13 route bằng nội dung minh họa, không dùng dữ liệu thật.
4. Chụp một focus state và một primary action disabled.
5. Kiểm dấu tiếng Việt, horizontal overflow, active navigation, một trial badge,
   bốn dashboard cards và wording non-tech.

Screenshot chỉ lưu/chia sẻ theo quyền kiểm soát của Project Owner; không đưa
ảnh có dữ liệu thật vào repo hoặc Codex.

Không đánh dấu checklist bằng kết quả test của Codex; Project Owner tự xác nhận
trong lần chạy local.
