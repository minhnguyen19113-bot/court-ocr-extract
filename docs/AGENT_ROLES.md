# Agent Roles

Last updated: 2026-07-07

These roles guide Codex behavior. They are not separate programs.

## Planner Agent

Responsibilities:

- Read repo and project memory.
- Plan scope.
- Identify files to inspect and files allowed to modify.
- Do not edit code.

Use before:

- Rebuilds.
- Cleanup.
- Large module changes.

Output:

- Plan.
- Scope.
- Risks.
- Files to inspect.
- Files allowed to modify.

## Repo Cleaner Agent

Responsibilities:

- Classify files/folders.
- Find duplicate/conflict areas.
- Propose move/archive/remove actions.
- Do not delete without approval.

Output:

- Cleanup table.
- Safe-to-remove candidates.
- Legacy candidates.
- Main path candidates.

## Surya OCR Agent

Responsibilities:

- Implement/check Surya OCR backend after approval.
- Create `OCRCacheRecord` from Surya output.
- Create bbox overlay and text review output.
- Do not use Tesseract/PaddleOCR as main path.

Output:

- OCR cache.
- Bbox overlay.
- Page text markdown/json.
- Terminal summary.
- Debug UI.

## VLM Pipeline Agent

Responsibilities:

- Implement/check VLM end-to-end benchmark path.
- Avoid cloud calls by default.
- Create output JSON/evidence/debug UI.
- Compare with Surya path when requested.

Output:

- VLM response.
- Parsed JSON.
- Validation warnings.
- Debug UI.

## Local LLM Extraction Agent

Responsibilities:

- Configure Qwen local through vLLM, Ollama, or local OpenAI-compatible endpoint.
- Enforce strict JSON.
- Add retry/repair if needed.
- Chunk long OCR text if needed.
- Require evidence for every field.

Output:

- Extraction JSON.
- JSON valid status.
- Evidence coverage.
- Warning summary.

## Validation / Anti-Hallucination Agent

Responsibilities:

- Evidence source matching.
- Fuzzy evidence matching.
- Duplicate participant checks.
- Role/date/id validation.
- `needs_review` rules.
- Low OCR confidence propagation.

Output:

- Validation report.
- Warning codes.
- QA metrics.

## Visual QA Agent

Responsibilities:

- Render/preprocess/OCR/extraction debug UI.
- Before/after preprocess view.
- Bbox overlay view.
- Text below or beside bbox.
- Evidence linked to page/line.
- Human review UX.

Output:

- `index.html`.
- Per-case review page.
- Overlay images.
- Manifests.

## Ezycloudx Runtime Agent

Responsibilities:

- Windows VM setup guidance.
- GPU checks.
- Surya checks.
- vLLM/Ollama checks.
- Run scripts.
- Transfer server.
- Do not upload data through Git.

Output:

- Runbook.
- Runtime check commands.
- Pilot commands.
- Troubleshooting notes.

## Security / Privacy Agent

Responsibilities:

- Prevent real data commits.
- Prevent PII logs.
- Prevent Codex from reading real outputs.
- Redact logs/reports.
- Check `.gitignore`.

Output:

- Security checklist.
- Suspicious file report.

## Docs / Memory Agent

Responsibilities:

- Update `PROJECT_STATE`, `TASKS`, `CODEX_HANDOFF`, and `CHANGELOG_AI`.
- Sync docs after each task.
- Create short handoff for the next Codex session.

Output:

- Updated memory files.
- Next-step summary.

Yêu cầu ngôn ngữ/report:

- Báo cáo cho Project Owner/ChatGPT phải viết bằng tiếng Việt.
- Heading report phải dùng tiếng Việt.
- Chỉ giữ tiếng Anh cho tên kỹ thuật chuẩn như file path, class, function, CLI command, env var, model name, package name, schema field.
- Không dùng report nửa Anh nửa Việt.
- Sau mỗi task, dùng template `# BÁO CÁO TASK` trừ khi Project Owner yêu cầu format khác.

## Required Codex Memory Reads

Before every task:

- `AGENTS.md`
- `docs/PROJECT_STATE.md`
- `docs/DECISIONS.md`
- `docs/TASKS.md`
- `docs/CODEX_HANDOFF.md`
- `docs/ARCHITECTURE.md`
- `docs/PIPELINE_SPEC.md`
- `docs/CLEANUP_PLAN.md` if cleanup/refactor is involved

After every task:

- Update `docs/PROJECT_STATE.md`.
- Update `docs/TASKS.md`.
- Update `docs/CHANGELOG_AI.md`.
- Update `docs/CODEX_HANDOFF.md`.
- Update `docs/DECISIONS.md` if a decision changed.
- Update `docs/CLEANUP_PLAN.md` if structure/classification changed.
