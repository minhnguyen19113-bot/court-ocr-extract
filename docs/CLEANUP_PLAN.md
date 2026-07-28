# Cleanup Plan

Last updated: 2026-07-10

Phase 1B applies main/default cleanup and canonical decisions. Repo cleanup on 2026-07-08 deleted local generated cache only; it did not delete, archive, or mass-move tracked source/docs.

Phase 1C adds architecture inventory, import graph, architecture guardrails, and production toolkit planning docs. It still does not approve deletion, archive, or mass-move of tracked source/docs.

Phase 1D removes old app folders after audit confirms they are not imported by the main CLI package path.

Phase 1E consolidates Excel/export behavior into `src/court_ocr_extract/excel_writer.py` and removes two duplicate paths after migrating every caller.

Phase 1F consolidates extractor backends into `src/court_ocr_extract/extractors/`, moves rule parsing under that package, and removes five duplicate/unimported extraction paths after caller migration.

FINAL EXCEL SCHEMA FIRST adds canonical `final_excel_schema.py` and `final_excel_builder.py`; `excel_writer.py` remains the sole workbook writer. These modules are `main_candidate`, not cleanup candidates.

TOOLKIT-1 adds `src/court_ocr_extract/evaluation/`, two CLI scripts và synthetic JSONL fixtures. Đây là `main_candidate` toolkit code; real manifests remain protected outside Git.

## Categories

- `main_candidate`: likely belongs in the rebuilt main path.
- `legacy_optional`: keep only if explicitly useful as legacy or benchmark support.
- `experimental`: keep for benchmark/prototype until reviewed.
- `duplicate_conflict`: overlaps another module and needs a canonical owner decision.
- `safe_to_remove_candidate`: appears removable after reviewer approval.
- `docs_memory`: repo memory and coordination docs.
- `tests_keep`: contract/control-flow tests to keep.
- `config_keep`: config/schema files to keep but possibly consolidate.
- `generated_junk`: local generated cache/build artifacts that should not be committed and may be deleted during cleanup.
- `unknown_need_review`: needs human decision before action.
- `removed_in_phase1d`: removed after Phase 1D audit; restore from Git history if needed.
- `removed_in_phase1e`: removed after Phase 1E caller/import audit; restore from Git history if needed.
- `removed_in_phase1f`: removed after Phase 1F extraction caller/import audit; restore from Git history if needed.

## Summary Counts

| Category | Count |
| --- | ---: |
| main_candidate | 22 |
| legacy_optional | 12 |
| experimental | 6 |
| duplicate_conflict | 5 |
| safe_to_remove_candidate | 0 |
| docs_memory | 17 |
| tests_keep | 17 |
| config_keep | 8 |
| generated_junk | 1 |
| unknown_need_review | 4 |
| removed_in_phase1d | 4 |
| removed_in_phase1e | 2 |
| removed_in_phase1f | 5 |

Counts are planning counts by grouped file/folder rows below, not exact file totals.

## Classification Table

| Path or group | Category | Notes | Proposed Phase 1B action |
| --- | --- | --- | --- |
| `AGENTS.md` | docs_memory | Guardrails and memory protocol. | Keep updated every task. |
| `docs/PROJECT_STATE.md` | docs_memory | Current project status. | Keep. |
| `docs/ARCHITECTURE.md` | docs_memory | Target architecture. | Keep. |
| `docs/DECISIONS.md` | docs_memory | Decision log. | Keep. |
| `docs/TASKS.md` | docs_memory | Task backlog. | Keep. |
| `docs/CHANGELOG_AI.md` | docs_memory | AI change log. | Keep. |
| `docs/CODEX_HANDOFF.md` | docs_memory | Next-session handoff. | Keep. |
| `docs/PIPELINE_SPEC.md` | docs_memory | Target pipeline spec. | Keep. |
| `docs/DATA_SCHEMA.md` | docs_memory | Target data contracts. | Keep. |
| `docs/DEBUG_OUTPUT_SPEC.md` | docs_memory | Target debug UI/output contract. | Keep. |
| `docs/TESTING.md` | docs_memory | Test policy. | Keep. |
| `docs/MODEL_BENCHMARK.md` | docs_memory | Model direction. | Keep. |
| `docs/RUNBOOK_EZYCLOUDX.md` | docs_memory | New runbook direction. | Keep. |
| `docs/SECURITY_PRIVACY.md` | docs_memory | Privacy and security rules. | Keep. |
| `docs/CLEANUP_PLAN.md` | docs_memory | Cleanup classification. | Keep. |
| `docs/AGENT_ROLES.md` | docs_memory | Agent role system. | Keep. |
| `docs/REPO_INVENTORY.md`, `docs/IMPORT_GRAPH.md`, `docs/LEGACY_ARCHIVE_PLAN.md`, `docs/PRODUCTION_TOOLKIT.md`, `docs/EVALUATION_PLAN.md`, `docs/GOLD_DATASET_GUIDE.md`, `docs/PRIVACY_REDACTION_PLAN.md`, `docs/OBSERVABILITY_PLAN.md`, `docs/MLOPS_PLAN.md` | docs_memory | Phase 1C architecture audit, repo slimming plan, production toolkit, evaluation, privacy, observability, and MLOps planning. | Keep and update when architecture/runtime decisions change. |
| `src/court_ocr_extract/pdf/`, `src/court_ocr_extract/pdf_render.py` | duplicate_conflict | Render logic appears split. | Choose canonical render package. |
| `src/court_ocr_extract/preprocess.py`, `image_preprocess.py`, `image_processing/` | duplicate_conflict | Preprocess/enhance logic overlaps. | Consolidate behind one preprocess API. |
| `src/court_ocr_extract/ocr/` | main_candidate | Newer OCR adapter/schema package. | Prefer for rebuild after review. |
| `src/court_ocr_extract/ocr_backends/surya_ocr.py`, `ocr_surya.py`, `ocr/surya_adapter.py` | duplicate_conflict | Multiple Surya paths. | Pick one Surya adapter and map to OCRCacheRecord. |
| `src/court_ocr_extract/ocr_cache.py` | main_candidate | OCR cache contract. | Keep and align with Surya/VLM output. |
| `src/court_ocr_extract/ocr_backends/tesseract_ocr.py` | legacy_optional | Tesseract backend only; not main/default path. | Keep temporarily as legacy optional. |
| `src/court_ocr_extract/ocr_backends/google_*`, `openai_vision_ocr.py`, `gemini_document_ocr.py` | legacy_optional | Cloud OCR adapters. | Keep opt-in benchmark only or archive. |
| `src/court_ocr_extract/vlm_backends/`, `vlm_page_reader.py` | experimental | VLM benchmark bridge exists. | Keep as benchmark, add validation parity later. |
| `src/court_ocr_extract/extractors/direct_vision_extractor.py` | experimental | Direct vision extraction path. | Keep for VLM benchmark review. |
| `scripts/smoke_vlm_synthetic.py`, `tests/test_vlm_contract.py` | experimental | Synthetic VLM contract only. | Keep; do not use for real quality. |
| `src/court_ocr_extract/local_llm/` | main_candidate | Local LLM client/parser/prompt builder used by typed compatibility adapter. | Keep; strict JSON/evidence hardening cần Phase 3A. |
| `src/court_ocr_extract/extraction_pipeline.py`, `src/court_ocr_extract/extractors/` | main_candidate | Canonical orchestrator và backend package sau Phase 1F. | Keep; mọi backend mới phải theo `ExtractorBackend`. |
| `src/court_ocr_extract/evaluation/`, `scripts/check_gold_manifest.py`, `scripts/evaluate_gold_manifest.py` | main_candidate | TOOLKIT-1 manifest/metrics/privacy/report code. | Keep lightweight; không thêm heavy tracking dependency ở phase này. |
| `tests/fixtures/*manifest_synthetic.jsonl` | tests_keep | Redacted synthetic evaluation contracts. | Keep; không thay bằng real gold/prediction data. |
| `src/court_ocr_extract/extraction/merge.py`, `schemas.py`, `__init__.py` | legacy_optional | Typed merge/schema compatibility helpers; không còn sở hữu extractor backend. | Giữ cho legacy typed pipeline; review riêng khi pipeline cũ được retire. |
| `src/court_ocr_extract/extraction/gliner_extractor.py` | experimental | Optional GLiNER support có behavior riêng. | Giữ experimental; không coi là canonical backend. |
| `src/court_ocr_extract/extraction/base.py`, `extraction/local_llm_extractor.py`, `extraction/rule_support.py`, `extractor.py`, `llm.py` | removed_in_phase1f | Duplicate/unimported paths đã migrate vào canonical `extractors/`. | Đã xóa; restore bằng Git history trước Phase 1F nếu cần. |
| `src/court_ocr_extract/validation.py`, `validator.py`, `extraction/validators.py` | duplicate_conflict | Validation split across modules. | Choose canonical validation package. |
| `src/court_ocr_extract/excel_writer.py` | main_candidate | Canonical Excel writer duy nhất sau Phase 1E; hỗ trợ draft records và typed `ExtractionResult`. | Keep; chỉ mở rộng schema qua phase được duyệt. |
| `src/court_ocr_extract/final_excel_schema.py`, `final_excel_builder.py` | main_candidate | Canonical 14-column final schema và rule-anchor row mapping; không chứa debug columns. | Keep; mọi final exporter dùng chung contract này. |
| `src/court_ocr_extract/excel.py`, `src/court_ocr_extract/export/excel_writer.py` | removed_in_phase1e | Caller đã migrate sang canonical path; không cần compatibility wrapper. | Đã xóa; restore bằng Git history trước Phase 1E nếu cần. |
| `src/court_ocr_extract/qa.py`, `scripts/qa_output.py`, `scripts/qa_batch_output.py` | main_candidate | QA output pieces exist. | Keep and align report schema. |
| `src/court_ocr_extract/visual_debug.py`, `review_html.py`, `evidence_viewer.py`, `extraction_preview.py` | main_candidate | Debug/review UI pieces. | Keep and connect bbox/evidence views. |
| `src/court_ocr_extract/remote_worker/`, `transfer.py`, `scripts/transfer_server.py` | main_candidate | Ezycloudx/remote worker support. | Keep, review fallback policy. |
| `src/court_ocr_extract/settings.py` | main_candidate | Canonical rebuild config after Phase 1B. | Keep as default source for new work. |
| `src/court_ocr_extract/config.py` | legacy_optional | Compatibility module for older imports. | Do not expand unless necessary; consolidate later. |
| `config/*.yaml`, `config/extraction_schema.json`, `templates/excel_columns.json` | config_keep | Config/schema definitions. | Keep, update defaults after approval. |
| `config/model_config.yaml`, `config/local_model.yaml` | config_keep | Model guidance partly outdated. | Align to Qwen2.5 direction. |
| `README.md`, `docs/ezycloudx_runbook.md`, `docs/ezycloudx_setup.md`, `docs/visual_qa_guide.md` | docs_memory | Phase 1B cleaned main defaults to Surya/VLM direction. | Keep current; update when runtime wiring changes. |
| `scripts/run_sample_windows.ps1`, `scripts/run_full_windows.ps1` | main_candidate | Defaults cleaned to Surya target; VLM branch guarded as not wired. | Keep as target pilot/full wrappers. |
| `scripts/repo_inventory.py`, `scripts/import_graph.py`, `scripts/check_architecture_guardrails.py` | main_candidate | Phase 1C safe architecture audit/guardrail tooling. | Keep; run before cleanup/archive decisions. |
| `scripts/ezycloudx_*` except removed old API launchers | unknown_need_review | Mixed setup/run scripts still need later review. `scripts/ezycloudx_run_api.sh` and `scripts/ezycloudx_run_api_windows.ps1` were removed in Phase 1D because they launched deleted `app_fastapi`. | Review and split setup/check/run commands. |
| `scripts/debug_5_pdfs_bbox.py` | legacy_optional | Name suggests real PDF debug workflow. | Review for safety before use. |
| `app/`, `app_fastapi/`, `app_streamlit/` | removed_in_phase1d | Old UI/app folders were not imported by main `src/`/CLI path. | Removed; restore from Git history before Phase 1D commit if needed. |
| `docs/streamlit_vs_fastapi.md` | removed_in_phase1d | Old UI doc instructed running removed app folders. | Removed; main docs now point to CLI/rebuild path. |
| `templates/upload.html` | removed_in_phase1d | Template was only used by removed `app/main.py`. | Removed; `templates/excel_columns.json` remains config_keep. |
| `streamlit` and `jinja2` optional web dependencies | removed_in_phase1d | Only old UI folders used them. | Removed from `pyproject.toml`; FastAPI/uvicorn remain for supported remote worker tooling. |
| `prompts/direct_vision_extraction_prompt.vi.md` | experimental | Direct vision prompt. | Keep for VLM benchmark. |
| `prompts/*local*`, `prompts/*json*`, `prompts/extraction_prompt.vi.md` | main_candidate | Local extraction prompt assets. | Keep and align with strict evidence JSON. |
| `tests/*.py` | tests_keep | Contract/control-flow tests. | Keep. |
| `tests/fixtures/*` | tests_keep | Non-real fixtures. | Keep only minimal synthetic content. |
| `requirements*.txt`, `pyproject.toml`, `Dockerfile.gpu` | config_keep | Dependency/runtime definitions. | Keep; update defaults after architecture decision. |
| `.env.example`, `.gitignore` | config_keep | Example env and ignore rules. `.env.example` now points to Surya target and cloud disabled defaults. | Keep, verify no cloud/default conflict. |
| `.env` | unknown_need_review | Local secret file; do not read. | Never commit; check only by path. |
| `.venv/`, `.pytest_cache/`, `__pycache__/`, `.ruff_cache/`, `.mypy_cache/` | generated_junk | Local environment/cache folders; `.venv/` itself is not deleted by Codex, but generated cache folders are safe to clean. | Delete generated cache folders during cleanup; never commit. |
| `data/`, `outputs/`, `logs/`, `work/`, `models/` | unknown_need_review | Protected or generated/sensitive areas. | Do not inspect in Codex; cleanup by owner only. |

## Major Conflicts Found

- Tesseract-as-default: cleaned in Phase 1B. Remaining Tesseract references should be legacy optional only.
- PaddleOCR: no safe code/docs references found in Phase 1A scan.
- VLM: useful benchmark modules exist, but they must not become unvalidated main path by accident.
- Cloud adapters: OpenAI/Gemini/Google OCR/extraction adapters exist and must remain opt-in.
- Duplicate extractor: resolved in Phase 1F; backend ownership thuộc `extractors/`, orchestrator thuộc `extraction_pipeline.py`.
- Duplicate Excel writer: resolved in Phase 1E; `excel_writer.py` là canonical duy nhất, hai path cũ đã xóa.
- Settings/config conflict: `settings.py` is canonical; `config.py` remains compatibility until consolidation.
- Old app folders: removed in Phase 1D after no main path import/reference was found.
- Run scripts conflicts: sample/full defaults cleaned to Surya target; VLM branch is explicitly not wired into these OCR-cache wrappers.

## Latest Cleanup Audit

- 2026-07-08: Deleted generated local cache folders in safe code/test/app roots.
- No tracked source/docs files were deleted because current cleanup classifications still show canonical conflicts or legacy/benchmark value.
- `ruff` audit was attempted but skipped because `ruff` is not installed in `.venv`.
- Protected real-data/output paths were not inspected or cleaned.

## Latest Phase 1C Architecture Audit

- Added safe inventory/import graph/architecture guardrail tooling.
- Added `docs/LEGACY_ARCHIVE_PLAN.md` as the review gate before any tracked archive/delete action.
- Trước Phase 1D/1E, warnings gồm old app và duplicate Excel; hai nhóm này đã được xử lý. Warnings còn lại gồm duplicate Surya/validation, opt-in cloud adapters, và VLM benchmark path.
- No tracked source/docs files were deleted, archived, or mass-moved.

## Latest Phase 1D Old App Cleanup

- Removed `app/`, `app_fastapi/`, and `app_streamlit/`.
- Removed stale old-app launch/doc/template artifacts: `scripts/ezycloudx_run_api.sh`, `scripts/ezycloudx_run_api_windows.ps1`, `docs/streamlit_vs_fastapi.md`, and `templates/upload.html`.
- Removed `streamlit` and `jinja2` from optional `web` dependencies because they were only used by old app/UI folders.
- Did not touch Surya OCR backend, Local LLM extractor, Excel writer, VLM benchmark modules, or real-data folders.
- Restore path: use Git history before the Phase 1D commit if an old app is needed for reference.

## Latest Phase 1E Excel/Export Consolidation

- Migrate mọi runtime/test caller từ `court_ocr_extract.excel` và `court_ocr_extract.export.excel_writer` sang `court_ocr_extract.excel_writer`.
- Chuyển typed `ExtractionResult` mapping/writing vào canonical writer, giữ nguyên header và sheet contract hiện hữu.
- Xóa `src/court_ocr_extract/excel.py` và `src/court_ocr_extract/export/excel_writer.py`; không tạo wrapper vì không còn caller.
- Architecture guardrail fail nếu canonical writer thiếu hoặc legacy import quay lại; path compatibility còn tồn tại sẽ phát warning.
- Restore path: use Git history before the Phase 1E commit.

## Latest Phase 1F Extraction Consolidation

- Canonical orchestrator: `src/court_ocr_extract/extraction_pipeline.py`.
- Canonical package/base/Local LLM/rule helper: `src/court_ocr_extract/extractors/`.
- Typed compatibility behavior nằm trong canonical `local_llm_extractor.py`; không tạo wrapper file.
- Xóa năm legacy/duplicate paths sau khi migrate mọi repo caller.
- Giữ merge/schema/validators/GLiNER, direct vision và cloud adapters theo vai trò riêng; cloud vẫn disabled/opt-in.
- Restore path: use Git history before the Phase 1F commit.

## No-Delete Rule

Ngoài các cleanup slice Phase 1D, Phase 1E và Phase 1F đã được Project Owner phê duyệt rõ, mọi tracked source/docs row còn lại chỉ là candidate classification. Không xóa hoặc move thêm tracked source/docs nếu chưa có approval riêng. Generated local cache folders có thể được dọn trong cleanup an toàn.

## Web Demo Platform Phase 0.5 structure

- `ops/web_demo/docker-compose.postgres.yml`: `config_keep`, local-only PostgreSQL
  smoke helper; không chứa OCR/GPU/LLM service.
- `ops/web_demo/.postgres-data/`: `generated_junk`, đã ignore; phải xóa sau smoke.
- `alembic/versions/0002_phase0_tables.py`: `main_candidate`, explicit reviewed migration
  cho 39 Phase 0 tables; không archive/delete khi Phase 0 còn active.
- Không có tracked file bị xóa, mass-move hoặc archive trong Phase 0.5.

## Web Demo Platform Phase 0.6 structure

- `docs/web_demo/CODEX_OPERATING_RULES.md`, `OPERATIONS_RUNBOOK.md`,
  `PORTS_AND_NETWORK.md`, `TROUBLESHOOTING.md`: `docs_memory`, giữ làm operational
  boundary và Project Owner handoff.
- `scripts/web_demo/check_prerequisites.ps1`: `main_candidate`, helper read-only;
  không start/stop service hoặc thay đổi máy.
- `tests/web/frontend/test_operator_runtime_contract.py`: `tests_keep`, static
  protection cho docs, loopback mapping, troubleshooting codes và helper boundary.
- `apps/web/node_modules/`, `.next/`, coverage và Python cache vẫn là
  `generated_junk`; không track và dọn sau validation.
- Không xóa, mass-move hoặc archive tracked source trong Phase 0.6.

## Web Demo Platform Phase 0.6 continuation structure

- `apps/web/package-lock.json`: `config_keep`, lockfile v3 do npm `11.16.0` tạo;
  không sửa thủ công hoặc xóa sau validation.
- `apps/web/.eslintrc.json`: `removed_in_phase0_7`; được thay sau khi
  `eslint.config.mjs` native flat config đã pass, tránh hai nguồn cấu hình.
- `apps/web/node_modules/`, `.next/`, `.npm-cache/`, coverage,
  `tsconfig.tsbuildinfo` và Python cache: `generated_junk`; không track và dọn sau
  test/build.
- Không xóa, mass-move hoặc archive tracked source trong continuation.

## Web Demo Platform Phase 0.7 structure

- `apps/web/eslint.config.mjs`: `config_keep`, native ESLint 10 flat config cho
  JS, TypeScript, React Hooks và Next rules.
- `apps/web/package.json`, `apps/web/package-lock.json`: `config_keep`, exact
  direct pins và ba transitive security overrides có removal condition.
- `docs/web_demo/FRONTEND_DEPENDENCY_SECURITY.md`: `docs_memory`, canonical
  frontend advisory baseline, remediation và cadence record.
- `apps/web/node_modules/`, `.next/`, `.npm-cache/`, coverage và
  `tsconfig.tsbuildinfo`: `generated_junk`; dọn sau acceptance.
- Phase 0.7 chỉ xóa một deprecated config file sau khi replacement pass; không
  mass-move/archive source hoặc đụng core parser/OCR.

## Web Demo Platform Phase 0.8 structure

- `apps/web/components/icons.tsx`, `environment-badge.tsx`,
  `user-menu-placeholder.tsx`, `primary-action.tsx`, `section-card.tsx` và
  `summary-card.tsx`: `main_candidate`, shared UI primitives cho shell/routes.
- `lucide-react@1.27.0`: `config_keep`, exact icon dependency; review/gỡ nếu
  framework cung cấp icon system tương đương và full validation vẫn pass.
- `docs/web_demo/UI_DESIGN_SYSTEM.md`,
  `LEGAL_UI_REFERENCE_PRINCIPLES.md`, `VISUAL_QA_CHECKLIST.md`: `docs_memory`.
- `tests/web/frontend/test_phase08_ui_contract.py`: `tests_keep`, static UI/UX
  acceptance, không phải browser visual test.
- `apps/web/node_modules/`, `.next/`, coverage, `.npm-cache/` và
  `tsconfig.tsbuildinfo`: `generated_junk`; dọn sau validation.
- Không xóa/mass-move/archive tracked source và không đụng core parser/OCR.
