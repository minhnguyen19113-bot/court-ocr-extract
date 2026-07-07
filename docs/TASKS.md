# Tasks

Last updated: 2026-07-07

## Phase 1A

- [x] Record project reorientation in repo memory.
- [x] Define Codex memory protocol.
- [x] Define agent role system.
- [x] Classify current repo files/folders for cleanup planning without deletion.
- [x] Add lightweight project snapshot script.
- [x] Add lightweight repo guardrail script.
- [x] Add focused tests for new scripts.
- [x] Reviewer approval for Phase 1B.

## Phase 1B

- [x] Clean docs and runbooks so Tesseract is no longer presented as default.
- [x] Clean `.env.example` so Surya is the target OCR default and cloud remains disabled.
- [x] Choose `src/court_ocr_extract/settings.py` as canonical config.
- [x] Mark `src/court_ocr_extract/config.py` as compatibility/legacy.
- [x] Choose `src/court_ocr_extract/excel_writer.py` as canonical Excel writer.
- [x] Update run scripts default backend to Surya target.
- [x] Keep legacy files in place; no deletion or mass move.

## Phase 1C / Phase 2 Candidates

Do not start without Project Owner / ChatGPT approval.

- Archive or move legacy app folders and legacy backends.
- Consolidate Surya OCR adapter path.
- Define and implement real Surya OCR cache contract.
- Expand debug UI around bbox/evidence/QA links.
- Choose canonical extraction package/API.
- Consolidate duplicate Excel/export wrappers.

## Memory/Reporting Rules

- [x] Add project-wide Vietnamese reporting rule.
- [x] Add standard Vietnamese task report template.
- [x] Record that technical identifiers remain in English when they are standard names.
- [x] Confirm no pipeline code change, no deletion, and no real-data run for this memory-only update.

## Backlog

- Local Qwen runtime hardening with strict JSON, retries, and evidence coverage.
- VLM benchmark harness with comparable QA output.
- Gold dataset workflow outside Codex for real quality assessment.
- Ezycloudx runtime checks for GPU, Surya, vLLM/Ollama, and transfer server.
