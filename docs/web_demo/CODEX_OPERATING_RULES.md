# Quy tắc vận hành dành cho Codex trên web branch

## 1. Phạm vi

Quy tắc này áp dụng cho mọi task chạm vào `apps/web/`,
`src/court_ocr_extract/web_api/`, `ops/web_demo/` hoặc `docs/web_demo/`. Các
guardrail core và privacy trong root `AGENTS.md` vẫn giữ nguyên.

## 2. Phân công trách nhiệm

Codex được phép:

- inspect và sửa code, config, test, docs trong scope đã duyệt;
- chạy lệnh kiểm thử hữu hạn tự kết thúc như `npm install`, `npm ci`,
  `npm audit`, `npm test`, typecheck, lint, build, pytest, compileall và
  guardrails khi runtime tương ứng đã có;
- tạo runbook và báo cáo lệnh để Project Owner tự vận hành.

Project Owner là người duy nhất:

- mở hoặc đóng Docker Desktop;
- khởi động hoặc dừng PostgreSQL;
- khởi động hoặc dừng FastAPI và Next.js;
- mở browser, bind network address, mở port, sửa Windows Firewall hoặc tạo
  tunnel;
- chạy dữ liệu thật, OCR, Surya/GPU hoặc deployment.

## 3. Lệnh Codex không được tự chạy

Codex không tự chạy:

- `docker`, `docker compose`, PostgreSQL/`psql` runtime command;
- `npm run dev`, `npm start`, `next dev`, `next start`;
- `uvicorn`, `fastapi dev` hoặc web server khác;
- browser, firewall, port-forward, tunnel hoặc process nền;
- OCR, Surya inference, GPU, LLM, cloud API hoặc dữ liệu thật.

Codex không giữ process nền sau task và không mở port để kiểm thử demo.

## 3a. Git performance policy

- Không dùng git diff trong web worktree vì gây chậm/khựng trên máy Project Owner.
- Dùng `git status --short`, `git status --porcelain=v1`, `git ls-files -m`,
  `git ls-files --deleted` và `git ls-files --others --exclude-standard`.
- Text hygiene dùng `scripts/check_text_hygiene.py`; không thay bằng lệnh Git nặng.

## 4. Network mặc định

- Local demo chỉ bind `127.0.0.1`.
- Không tự bind `0.0.0.0`.
- Không mở Windows Firewall hoặc public Internet.
- LAN/public deployment là task riêng, chỉ sau authentication, authorization,
  HTTPS và security review.
- Artifact storage không được public trực tiếp.

## 5. Ngoại lệ

Ngoại lệ chỉ có hiệu lực khi Project Owner cho phép rõ trong đúng task hiện tại,
với target và hành động cụ thể. Quyền từ task trước không được mang sang task
mới. Ngoại lệ không làm vô hiệu guardrail real-data/core của root `AGENTS.md`.

## 6. Cách bàn giao

Codex phải ghi các lệnh start/stop vào `docs/web_demo/OPERATIONS_RUNBOOK.md`,
không tự chạy các lệnh đó. Báo cáo phải nêu rõ service nào đã hoặc chưa được
Codex chạy, process nền còn lại và network boundary.
