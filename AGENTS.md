# Repository Guardrails For Codex

- Do not open, read, OCR, grep, parse, inspect, summarize, or quote any real PDF or derived real-data artifact in `data/raw_pdfs/`, `data/private_pdfs/`, `data/images/`, `data/processed_images/`, `data/ocr_raw/`, `data/ocr_corrected/`, or `outputs/`.
- Exception: Codex may create and inspect artifacts under explicit synthetic smoke paths such as `outputs/debug_visual/synthetic_smoke/`, `outputs/extraction_draft/synthetic_smoke/`, `outputs/excel/synthetic_smoke.xlsx`, and `outputs/qa/synthetic_smoke_report.json`, because these are generated from non-real contract fixtures by `python -m scripts.smoke_synthetic_debug`.
- Work only with code, config, docs, prompts, and minimal contract fixtures.
- Do not use fake/sample fixtures to judge OCR or extraction quality. Real quality validation must be run by the user on real court PDFs outside Codex.
- If automated tests need input, use minimal non-real contract fixtures under `tests/fixtures/`; these fixtures are only for schema/control-flow tests.
- Do not use names, addresses, CCCD/CMND numbers, case details, or wording copied from real people or real PDFs.
- Do not print full OCR text, full names, addresses, CCCD/CMND, or sensitive file names in logs.
- Do not call cloud LLM APIs by default. Cloud LLM adapters must remain opt-in and disabled by config.
- Do not run debug or batch OCR scripts on real user folders inside Codex. The user may run the real-data pilot/full workflow directly outside Codex.

## Project Direction

- Project Owner owns direction, runs real-data workflows on the Ezycloudx VM or local machine, opens outputs, and decides whether quality is acceptable.
- ChatGPT is Architect / Reviewer / Prompt Designer and does not directly edit the repo.
- Codex is Repo Manager / Implementation Agent. Codex edits code/docs/tests only inside explicit task scope and reports files changed, commands run, test results, and risks.
- The rebuild has two approved candidate paths:
  - Main candidate: render PDF pages, optional preprocess, Surya OCR, OCR cache, normalize/split, rule extraction for easy fields, local LLM extraction for hard fields, evidence validation, Excel, QA report, debug UI/human review.
  - Benchmark path: local VLM end-to-end page/image extraction, validation, Excel, QA report, debug UI/human review.
- Tesseract is legacy only, PaddleOCR is not part of the rebuild path, and cloud OpenAI/Google/Gemini OCR or extraction must stay disabled by default unless the Project Owner explicitly requests an opt-in benchmark.
- Synthetic smoke fixtures are for schema/control-flow only. They must never be used to judge real OCR or extraction quality.

## Codex Memory Protocol

Before every task, Codex must read:

- `AGENTS.md`
- `docs/PROJECT_STATE.md`
- `docs/DECISIONS.md`
- `docs/TASKS.md`
- `docs/CODEX_HANDOFF.md`
- `docs/ARCHITECTURE.md`
- `docs/PIPELINE_SPEC.md`
- `docs/CLEANUP_PLAN.md` when the task involves cleanup, refactor, moving files, or deleting files
- `docs/REPO_INVENTORY.md`, `docs/IMPORT_GRAPH.md`, `docs/LEGACY_ARCHIVE_PLAN.md`, and `docs/PRODUCTION_TOOLKIT.md` when the task involves architecture audit, repo slimming, production readiness, or archive planning
- `docs/EVALUATION_PLAN.md`, `docs/GOLD_DATASET_GUIDE.md`, `docs/PRIVACY_REDACTION_PLAN.md`, `docs/OBSERVABILITY_PLAN.md`, and `docs/MLOPS_PLAN.md` when the task involves evaluation, privacy, observability, model/runtime governance, or real-data pilot planning

## Quy tắc ngôn ngữ

- Mọi báo cáo cho Project Owner/ChatGPT phải dùng tiếng Việt.
- Heading report dùng tiếng Việt.
- Chỉ giữ tiếng Anh cho tên kỹ thuật không nên dịch: file path, class, function, CLI command, env var, model name, package name, schema field.
- Không dùng format report nửa Anh nửa Việt.
- Nếu prompt từ ChatGPT có heading tiếng Anh, Codex vẫn phải trả về bản tiếng Việt trừ khi được yêu cầu khác.
- Project memory docs ưu tiên tiếng Việt.
- Code comments có thể dùng tiếng Anh nếu đang theo phong cách codebase, nhưng user-facing docs/report phải là tiếng Việt.

## Template report tiếng Việt

```markdown
# BÁO CÁO TASK

## 1. Tóm tắt

## 2. File đã thay đổi

## 3. Quyết định đã áp dụng

## 4. Lệnh đã chạy

## 5. Kết quả test

## 6. Output/debug đã tạo

## 7. Rủi ro còn lại

## 8. Câu hỏi cần quyết định

## 9. Bước tiếp theo đề xuất
```

After every task, Codex must update:

- `docs/PROJECT_STATE.md`
- `docs/TASKS.md`
- `docs/CHANGELOG_AI.md`
- `docs/CODEX_HANDOFF.md`
- `docs/DECISIONS.md` if a new decision was made
- `docs/CLEANUP_PLAN.md` if file/folder structure or cleanup classification changed
- Phase 1C blueprint docs when architecture inventory, archive planning, production toolkit, evaluation, privacy, observability, or MLOps guidance changed

If a task edits code, Codex must also:

- Update the relevant docs.
- Run the focused tests or checks that match the change.
- Report exact commands and results.
- Avoid saying the task is done without test/log/output evidence.
- Run `python -m scripts.check_architecture_guardrails` when the task touches architecture defaults, repo slimming, OCR/backend selection, cloud/default behavior, protected path policy, or production toolkit docs.

## Cleanup Approval Rule

- Do not delete, mass-move, archive, or rewrite large areas of code without explicit Project Owner approval.
- Phase 1B cleaned main defaults and canonical config/writer decisions. Do not delete or mass-move legacy files until a later cleanup phase is approved.
- Cleanup candidates must be reported in `docs/CLEANUP_PLAN.md` before any destructive action.

## Web Demo Runtime Boundary

- Mọi agent làm việc trong `apps/web/`, `src/court_ocr_extract/web_api/`,
  `ops/web_demo/` hoặc `docs/web_demo/` phải đọc
  `docs/web_demo/CODEX_OPERATING_RULES.md`.
- Codex chỉ sửa code/docs và chạy kiểm thử hữu hạn; Project Owner trực tiếp vận
  hành Docker, PostgreSQL, FastAPI, Next.js, browser, port và network.
- Không tự bind `0.0.0.0`; demo local mặc định dùng `127.0.0.1`.
- Không dùng git diff trong web worktree vì gây chậm/khựng trên máy Project Owner.
