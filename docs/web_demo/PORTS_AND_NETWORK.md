# Port và network boundary cho web demo

## 1. Port map hiện tại

| Thành phần | Địa chỉ mặc định | Port | Nguồn cấu hình |
| --- | --- | --- | --- |
| Next.js frontend | `127.0.0.1` | `3000` | `FRONTEND_HOST`, `FRONTEND_PORT` và CLI Project Owner |
| FastAPI backend | `127.0.0.1` | `8000` | `WEB_API_HOST`, `WEB_API_PORT` và CLI Project Owner |
| PostgreSQL development | `127.0.0.1` | `55432` | `WEB_POSTGRES_PORT` trong compose |
| API contract | `http://127.0.0.1:8000/api/v1` | `8000` | FastAPI `/api/v1` |
| Next server rewrite | `/api/v1` → `http://127.0.0.1:8000/api/v1` | `3000` → `8000` | `NEXT_PUBLIC_API_BASE_URL`, `WEB_API_ORIGIN` |

Compose PostgreSQL phải dùng:

```yaml
ports:
  - "127.0.0.1:${WEB_POSTGRES_PORT:-55432}:5432"
```

Không bỏ phần `127.0.0.1:` khỏi mapping.

## 2. Đổi port local

Đổi port trong đúng PowerShell do Project Owner vận hành, trước khi start:

```powershell
$env:WEB_POSTGRES_PORT="55433"
$env:WEB_API_PORT="8001"
$env:FRONTEND_PORT="3001"
$env:WEB_API_ORIGIN="http://127.0.0.1:8001"
```

Sau đó thay port tương ứng trong các lệnh start và URL kiểm tra. Không commit
credential hoặc `.env.local`.

`NEXT_PUBLIC_API_BASE_URL` mặc định là `/api/v1`. Next server rewrite prefix này
tới `WEB_API_ORIGIN`, mặc định `http://127.0.0.1:8000`. Đây là server-only
environment variable; không dùng `NEXT_PUBLIC_` cho backend origin. Phase 0.6 chỉ
chấp nhận `http://127.0.0.1:<port>` và từ chối origin khác. Browser giữ same-origin,
FastAPI không bật CORS và không cần wildcard CORS.

## 3. Kiểm tra port bị chiếm

Kiểm tra listener bằng PowerShell:

```powershell
Get-NetTCPConnection -State Listen -LocalPort 3000,8000,55432 |
  Select-Object LocalAddress,LocalPort,OwningProcess
```

Kiểm tra process giữ một PID đã xác định:

```powershell
Get-Process -Id <PID> |
  Select-Object Id,ProcessName,Path
```

Chỉ Project Owner quyết định dừng process sau khi xác nhận đúng owner và đúng
component. Helper của repo chỉ báo port đang dùng, không dừng process.

## 4. Loopback-only

- Frontend: `--hostname 127.0.0.1`.
- Backend: `--host 127.0.0.1`.
- PostgreSQL: compose bind `127.0.0.1`.
- Browser URL: `http://127.0.0.1:3000`.
- Proxied health URL: `http://127.0.0.1:3000/api/v1/system/health`.
- Không dùng `localhost` khi cần audit chính xác bind address; `127.0.0.1` là
  contract mặc định.

Loopback ngăn máy khác trong LAN truy cập trực tiếp. Đây là trạng thái bắt buộc
cho Phase 0.6.

## 5. LAN hoặc public network

Truy cập từ máy khác trong LAN sẽ cần thay bind address, firewall rule, CORS hoặc
reverse proxy và xác định trusted network. Những thay đổi đó làm tăng attack
surface và không được suy ra từ local demo.

Rủi ro khi bind `0.0.0.0`:

- mọi network interface có thể nhận kết nối;
- endpoint chưa authentication có thể bị người khác truy cập;
- metadata/capability contract có thể bị thu thập;
- dev server và error page có thể lộ thông tin kỹ thuật.

Rủi ro khi mở Windows Firewall hoặc Internet:

- port có thể bị truy cập ngoài ý muốn;
- HTTP không bảo vệ traffic;
- Phase 0 chưa có authentication, authorization, rate limit hoặc production
  hardening;
- artifact storage có nguy cơ bị public sai.

Trước mọi network deployment phải có authentication, authorization, HTTPS,
secret management, CORS/reverse-proxy policy, threat model và security review.
Artifact storage chỉ được truy cập qua authorized opaque-ID API trong phase sau,
không public directory trực tiếp.

**Public/network deployment: NOT APPROVED IN PHASE 0.6.**

Không có lệnh mở firewall, bind `0.0.0.0` hoặc tunnel trong runbook Phase 0.6.
