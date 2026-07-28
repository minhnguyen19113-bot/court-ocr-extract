# Runbook phát triển local

## 1. Boundary vận hành

Phase 0 chạy trên máy phát triển:

- không deploy;
- không cần GPU hoặc máy ảo;
- không chạy Docker GPU, Surya, OCR, LLM hoặc cloud;
- không dùng PDF/ảnh/output thật;
- chỉ dùng synthetic fixture cho schema/control-flow;
- không tự cài PostgreSQL, Docker hoặc Node system-wide.

Các lệnh web/database bên dưới chỉ chạy sau khi file/dependency tương ứng đã được tạo ở các bước implementation.

## 2. Environment placeholder

Config mẫu chỉ được chứa:

```dotenv
DATABASE_URL=
ARTIFACT_ROOT=
WEB_API_HOST=
WEB_API_PORT=
FRONTEND_API_BASE_URL=
```

Không điền credential thật vào file được commit. `ARTIFACT_ROOT` là cấu hình nội bộ; giá trị không được trả qua public API.

## 3. Backend development

Kiểm tra Python:

```text
python --version
```

Tạo virtual environment và cài dependency trong project:

```text
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e ".[web,dev]"
```

Không dùng system-wide install. Khi scaffold FastAPI đã tồn tại, chạy local loopback:

```text
python -m uvicorn court_ocr_extract.web_api.app:app --reload --host 127.0.0.1 --port 8000
```

Endpoint smoke:

```text
GET http://127.0.0.1:8000/api/v1/system/health
GET http://127.0.0.1:8000/api/v1/system/capabilities
GET http://127.0.0.1:8000/api/v1/system/schema
GET http://127.0.0.1:8000/api/v1/system/workflows
GET http://127.0.0.1:8000/api/v1/forms/capabilities
```

Phase 0 không gửi POST/PUT/PATCH/DELETE.

## 4. Backend tests

Chạy targeted test modules được tạo cho domain/database/API/form:

```text
python -B -m pytest <targeted-test-files> -q -p no:cacheprovider
```

`<targeted-test-files>` phải được thay bằng đường dẫn test thực tế trong báo cáo; không tuyên bố pass cho lệnh placeholder.

Sau khi targeted tests xanh, có thể chạy full safe suite nếu suite không gọi OCR/Docker/LLM/cloud:

```text
python -B -m pytest -q -p no:cacheprovider
```

Không thêm skip/xfail để che lỗi.

## 5. Database development

Runtime target là một PostgreSQL với logical schema `ingest`, `processing`, `review`, `core`, `forms`, `audit`. Project Owner chủ động provision PostgreSQL local hoặc container. Codex không tự cài system-wide.

Sau khi Alembic foundation tồn tại và `DATABASE_URL` đã được cung cấp an toàn:

```text
python -m alembic upgrade head
python -m alembic current
```

Tạo migration mới chỉ sau review model:

```text
python -m alembic revision --autogenerate -m "web platform foundation"
```

Phải review migration trước `upgrade`. SQLite chỉ dùng metadata/unit test, không dùng làm runtime database demo/production.

## 6. Frontend development

Kiểm tra runtime trước:

```text
node --version
npm --version
```

Không tự nâng cấp Node system-wide. Khi `apps/web/package.json` và lockfile đã tồn tại:

```text
cd apps/web
npm install
npm run dev
```

Ưu tiên `npm ci` khi lockfile đã ổn định:

```text
npm ci
npm run test
npm run build
```

Nếu Node/npm không có hoặc không tương thích, không chạy install; báo rõ frontend tests chưa chạy. Không dùng CDN runtime và không dùng version `latest`.

## 7. Verification cuối Phase 0

```text
python -B -m compileall src/court_ocr_extract -q
python -B -m scripts.check_repo_guardrails
python -B -m scripts.check_architecture_guardrails
python -B scripts/check_text_hygiene.py
git status --short
git ls-files -m
git ls-files --others --exclude-standard
```

Chỉ chạy full Python suite khi xác nhận không kích hoạt runtime thật. Kiểm kê scope
bằng status/listing nhẹ; không dùng lệnh Git tạo patch trong web worktree.

## 7a. Local launcher dành cho Project Owner

Project Owner xem `LOCAL_RUN_GUIDE.md` để dùng `start_local.ps1`, `status_local.ps1`
và `stop_local.ps1`. Codex chỉ chạy PowerShell AST/static tests, không gọi launcher
start. Known-error canonical nằm tại `KNOWN_ISSUES_AND_RECOVERY.md`.

## 8. Không xử lý sự cố bằng cách nới guardrail

- Không đọc protected real-data path để debug.
- Không public artifact directory.
- Không bật cloud/LLM mặc định.
- Không fake adapter/generation capability.
- Không sửa core parser để làm web test pass.
- Không deploy Phase 0.

## 9. PostgreSQL smoke cho Phase 0.5

Compose local chỉ dùng dữ liệu synthetic và không chứa OCR/GPU/LLM:

```text
docker compose -f ops/web_demo/docker-compose.postgres.yml up -d
$env:DATABASE_URL="postgresql+psycopg://web_demo_synthetic:local_development_only@localhost:55432/court_ocr_web_synthetic"
python -m alembic upgrade head
python -m alembic check
python -m alembic downgrade base
python -m alembic upgrade head
docker compose -f ops/web_demo/docker-compose.postgres.yml down
```

Chuỗi migration Phase 0 hiện là `0001_phase0_foundation` tạo sáu logical schema và
`0002_phase0_tables` tạo 39 bảng. Phase 0.5 đã smoke thành công hai lần upgrade và
một lần downgrade trên `postgres:16.4-bookworm`; bind directory
`ops/web_demo/.postgres-data/` là generated local state, đã được ignore và phải xóa
sau smoke.

## 10. Frontend acceptance và lockfile

Contract đã được xác nhận bằng system runtime tại
`C:\Program Files\nodejs`: Node `v24.18.0`, npm `11.16.0`. PowerShell audit ban đầu
chưa refresh `PATH`, nhưng prerequisite helper có fallback read-only tới system
installation. Codex Desktop bundled Node không được dùng.

`apps/web/package.json` chốt
`engines.node ^20.19.0 || ^22.13.0 || >=24`, `engines.npm >=11.16.0` và
`packageManager npm@11.16.0`. `package-lock.json` lockfile version 3 được npm tạo,
chỉ resolve từ `registry.npmjs.org`, không có local/file/link dependency hoặc
absolute user path. Workflow xác nhận:

```text
cd apps/web
npm install
npm ci
npm audit
npm audit --omit=dev
npm test
npm run typecheck
npm run lint
npm run build
```

Ngày 2026-07-27: Next `15.5.21`, React/React DOM `19.2.8`, Vitest `3.2.6` và
ESLint `10.8.0` native flat config đã được pin exact. `npm ci`, 6 Vitest tests,
TypeScript strict check, ESLint `--max-warnings=0` và Next production build đều
pass. Full audit và production audit đều `0 vulnerabilities`; build không gọi
backend. Xem `FRONTEND_DEPENDENCY_SECURITY.md` cho baseline 38 GHSA, override
rationale và cadence. Tuyệt đối không dùng `npm audit fix --force`.

`requirements-web.txt` tiếp tục là dependency group dùng chung cho web API và
`remote_worker`: việc bỏ `streamlit`/`jinja2` không ảnh hưởng `remote_worker`, còn
`fastapi`, `uvicorn` và `python-multipart` vẫn được giữ.

## 11. Runtime boundary Phase 0.7

Mọi lệnh start/stop database, backend, frontend và browser trong tài liệu này là
lệnh dành cho Project Owner. Codex không được tự chạy các lệnh đó. Quy tắc đầy đủ:

- `docs/web_demo/CODEX_OPERATING_RULES.md`;
- `docs/web_demo/OPERATIONS_RUNBOOK.md`;
- `docs/web_demo/PORTS_AND_NETWORK.md`;
- `docs/web_demo/TROUBLESHOOTING.md`.

Local default là `127.0.0.1`: frontend 3000, backend 8000 và PostgreSQL 55432.
Compose PostgreSQL bind explicit loopback. Public/LAN deployment chưa được phê
duyệt trong Phase 0.7.

System runtime ngày 2026-07-24 là Node `v24.18.0` và npm `11.16.0`; bundled runtime
không được dùng. Codex chỉ chạy install/test/build hữu hạn, không khởi động service,
browser hoặc listener. Frontend functional và dependency-security acceptance đã
đạt; local runtime/visual QA vẫn do Project Owner trực tiếp thực hiện.

## 12. Frontend–backend local integration

Frontend client mặc định dùng relative `/api/v1`. `next.config.mjs` rewrite
`/api/v1/:path*` tới `${WEB_API_ORIGIN}/api/v1/:path*`, với mặc định server-only
`WEB_API_ORIGIN=http://127.0.0.1:8000`. Phase 0.7 chỉ chấp nhận exact loopback HTTP
origin; origin không hợp lệ làm config fail-closed. Browser gọi same-origin nên
FastAPI không cần bật CORS. Build không yêu cầu backend đang chạy; khi runtime
backend không sẵn sàng, API-dependent panel vẫn phải fail thành controlled
unavailable state.
