# Production Toolkit

Last updated: 2026-07-08

## Mục tiêu

Toolkit này mô tả bộ việc cần có để đưa pipeline từ contract code sang pilot production có kiểm soát. Codex chuẩn bị code/docs/tests; Project Owner chạy dữ liệu thật trên Ezycloudx hoặc máy local kiểm soát.

## Luồng production mục tiêu

```text
PDF
-> render page image
-> optional preprocess
-> Surya OCR
-> OCR cache + bbox/evidence
-> normalize/split
-> rule extraction
-> local LLM extraction
-> validation/anti-hallucination
-> Excel
-> QA report
-> visual review
```

## Bộ command an toàn cho repo

```powershell
.\.venv\Scripts\python -B -m compileall src scripts -q
.\.venv\Scripts\python -B -m scripts.project_snapshot
.\.venv\Scripts\python -B -m scripts.check_repo_guardrails
.\.venv\Scripts\python -B -m scripts.check_architecture_guardrails
.\.venv\Scripts\python -B -m scripts.repo_inventory
.\.venv\Scripts\python -B -m scripts.import_graph
.\.venv\Scripts\python -B -m scripts.check_ocr_backend --backend surya
.\.venv\Scripts\python -B -m pytest -p no:cacheprovider
```

Các command trên không được dùng để kết luận chất lượng OCR thật.

## Gate production

| Gate | Owner | Điều kiện qua gate |
| --- | --- | --- |
| Repo safety | Codex | Guardrails pass, không có real-data path tracked/staged. |
| Runtime readiness | Project Owner | Ezycloudx cài Surya/local LLM đúng version và GPU ổn định nếu cần. |
| OCR pilot | Project Owner | Visual review xác nhận render, bbox, text, confidence usable. |
| Extraction pilot | Project Owner + Reviewer | Evidence coverage đủ, JSON hợp lệ, warning dễ hiểu. |
| Excel/QA pilot | Project Owner | Excel đúng schema, không rò PII qua log/report. |
| Full run | Project Owner | Chỉ chạy sau khi pilot được chấp nhận. |

## Roles khi vận hành

- Repo Manager: giữ guardrail, docs, tests, changelog.
- Runtime Operator: kiểm tra Ezycloudx, dependency, model server.
- OCR Reviewer: xem render/OCR bbox/text.
- Extraction Reviewer: kiểm field/evidence/warning.
- QA Owner: duyệt Excel/QA report.
- Privacy Owner: kiểm log/output trước khi chia sẻ.

## Không làm trong Codex

- Không chạy batch real PDFs.
- Không mở OCR cache/output thật.
- Không gọi cloud API mặc định.
- Không dùng synthetic smoke để kết luận quality thật.
