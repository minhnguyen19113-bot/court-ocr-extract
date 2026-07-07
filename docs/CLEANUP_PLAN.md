# Cleanup Plan

Last updated: 2026-07-07

Phase 1B applies main/default cleanup and canonical decisions. It does not delete, archive, or mass-move files.

## Categories

- `main_candidate`: likely belongs in the rebuilt main path.
- `legacy_optional`: keep only if explicitly useful as legacy or benchmark support.
- `experimental`: keep for benchmark/prototype until reviewed.
- `duplicate_conflict`: overlaps another module and needs a canonical owner decision.
- `safe_to_remove_candidate`: appears removable after reviewer approval.
- `docs_memory`: repo memory and coordination docs.
- `tests_keep`: contract/control-flow tests to keep.
- `config_keep`: config/schema files to keep but possibly consolidate.
- `unknown_need_review`: needs human decision before action.

## Summary Counts

| Category | Count |
| --- | ---: |
| main_candidate | 20 |
| legacy_optional | 12 |
| experimental | 6 |
| duplicate_conflict | 8 |
| safe_to_remove_candidate | 0 |
| docs_memory | 16 |
| tests_keep | 17 |
| config_keep | 8 |
| unknown_need_review | 6 |

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
| `src/court_ocr_extract/local_llm/` | main_candidate | Local LLM client/parser/prompt builder. | Keep and harden strict JSON. |
| `src/court_ocr_extract/extraction/local_llm_extractor.py` | main_candidate | Newer extraction package. | Prefer after canonical review. |
| `src/court_ocr_extract/extractors/local_llm_extractor.py` | duplicate_conflict | Older/parallel extractor path. | Compare then consolidate. |
| `src/court_ocr_extract/extraction/`, `extractor.py`, `extraction_pipeline.py` | duplicate_conflict | Rule/merge/extraction paths overlap. | Choose canonical extraction API. |
| `src/court_ocr_extract/validation.py`, `validator.py`, `extraction/validators.py` | duplicate_conflict | Validation split across modules. | Choose canonical validation package. |
| `src/court_ocr_extract/excel_writer.py` | main_candidate | Canonical Excel writer after Phase 1B. | Keep and extend only through approved schema work. |
| `src/court_ocr_extract/excel.py`, `export/excel_writer.py` | duplicate_conflict | Duplicate/legacy Excel writer paths overlap canonical writer. | Compare then consolidate/archive later. |
| `src/court_ocr_extract/qa.py`, `scripts/qa_output.py`, `scripts/qa_batch_output.py` | main_candidate | QA output pieces exist. | Keep and align report schema. |
| `src/court_ocr_extract/visual_debug.py`, `review_html.py`, `evidence_viewer.py`, `extraction_preview.py` | main_candidate | Debug/review UI pieces. | Keep and connect bbox/evidence views. |
| `src/court_ocr_extract/remote_worker/`, `transfer.py`, `scripts/transfer_server.py` | main_candidate | Ezycloudx/remote worker support. | Keep, review fallback policy. |
| `src/court_ocr_extract/settings.py` | main_candidate | Canonical rebuild config after Phase 1B. | Keep as default source for new work. |
| `src/court_ocr_extract/config.py` | legacy_optional | Compatibility module for older imports. | Do not expand unless necessary; consolidate later. |
| `config/*.yaml`, `config/extraction_schema.json`, `templates/excel_columns.json` | config_keep | Config/schema definitions. | Keep, update defaults after approval. |
| `config/model_config.yaml`, `config/local_model.yaml` | config_keep | Model guidance partly outdated. | Align to Qwen2.5 direction. |
| `README.md`, `docs/ezycloudx_runbook.md`, `docs/ezycloudx_setup.md`, `docs/visual_qa_guide.md` | docs_memory | Phase 1B cleaned main defaults to Surya/VLM direction. | Keep current; update when runtime wiring changes. |
| `scripts/run_sample_windows.ps1`, `scripts/run_full_windows.ps1` | main_candidate | Defaults cleaned to Surya target; VLM branch guarded as not wired. | Keep as target pilot/full wrappers. |
| `scripts/ezycloudx_*` | unknown_need_review | Mixed setup/run scripts. | Review and split setup/check/run commands. |
| `scripts/debug_5_pdfs_bbox.py` | legacy_optional | Name suggests real PDF debug workflow. | Review for safety before use. |
| `app/`, `app_fastapi/`, `app_streamlit/` | unknown_need_review | Multiple app folders. | Decide one UI/runtime owner. |
| `prompts/direct_vision_extraction_prompt.vi.md` | experimental | Direct vision prompt. | Keep for VLM benchmark. |
| `prompts/*local*`, `prompts/*json*`, `prompts/extraction_prompt.vi.md` | main_candidate | Local extraction prompt assets. | Keep and align with strict evidence JSON. |
| `tests/*.py` | tests_keep | Contract/control-flow tests. | Keep. |
| `tests/fixtures/*` | tests_keep | Non-real fixtures. | Keep only minimal synthetic content. |
| `requirements*.txt`, `pyproject.toml`, `Dockerfile.gpu` | config_keep | Dependency/runtime definitions. | Keep; update defaults after architecture decision. |
| `.env.example`, `.gitignore` | config_keep | Example env and ignore rules. `.env.example` now points to Surya target and cloud disabled defaults. | Keep, verify no cloud/default conflict. |
| `.env` | unknown_need_review | Local secret file; do not read. | Never commit; check only by path. |
| `.venv/`, `.pytest_cache/`, `__pycache__/` | unknown_need_review | Local generated folders. | Ignore, do not edit. |
| `data/`, `outputs/`, `logs/`, `work/`, `models/` | unknown_need_review | Protected or generated/sensitive areas. | Do not inspect in Codex; cleanup by owner only. |

## Major Conflicts Found

- Tesseract-as-default: cleaned in Phase 1B. Remaining Tesseract references should be legacy optional only.
- PaddleOCR: no safe code/docs references found in Phase 1A scan.
- VLM: useful benchmark modules exist, but they must not become unvalidated main path by accident.
- Cloud adapters: OpenAI/Gemini/Google OCR/extraction adapters exist and must remain opt-in.
- Duplicate extractor: `extraction/`, `extractors/`, `extractor.py`, and `extraction_pipeline.py`.
- Duplicate Excel writer: `excel_writer.py` is canonical; `excel.py` and `export/excel_writer.py` remain duplicate/legacy candidates.
- Settings/config conflict: `settings.py` is canonical; `config.py` remains compatibility until consolidation.
- Old app folders: `app/`, `app_fastapi/`, `app_streamlit/`.
- Run scripts conflicts: sample/full defaults cleaned to Surya target; VLM branch is explicitly not wired into these OCR-cache wrappers.

## No-Delete Rule

Every row above is a candidate classification only. Do not delete or move anything until the Project Owner approves Phase 1B cleanup scope.
