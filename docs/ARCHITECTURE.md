# Architecture

Last updated: 2026-07-14

## Target Principles

- Local-first processing by default.
- Every extracted field needs evidence.
- Debug output is mandatory for render, preprocess, OCR/VLM, extraction, validation, Excel, and QA.
- No silent fallback between OCR backends or extractor backends.
- Synthetic tests prove contracts only, not real OCR/extraction quality.
- Cloud APIs remain disabled unless explicitly enabled for a benchmark.

## Candidate Path A: Surya OCR + Local LLM

This is the main candidate because it is easier to debug than direct VLM extraction.

Flow:

```text
PDF
-> render page images
-> optional preprocess/enhance
-> Surya OCR
-> bbox/text/layout/reading order
-> OCRCacheRecord/text cache
-> normalize text
-> pre-content anchor/block segmentation
-> deterministic metadata and trial-panel extraction
-> deterministic defendant/participant block parsing + validators
-> optional Local LLM repair for one entity block at a time
-> evidence validation
-> Excel
-> QA report
-> debug UI/human review
```

Required debug links:

- Page image.
- OCR line IDs.
- Bbox coordinates.
- OCR confidence/layout metadata when available.
- Evidence for every field.
- QA warning codes and needs-review status.

## Candidate Path B: VLM End-to-End

This is a benchmark path, not the only main path.

Flow:

```text
PDF/page image
-> local VLM reads page directly
-> strict JSON extraction or OCR-compatible bridge
-> validation
-> Excel
-> QA report
-> debug UI/human review
```

VLM output must be validated with the same evidence, hallucination, and QA rules used by the Surya path.

## Current Module Map

Likely main candidates:

- PDF/render: `src/court_ocr_extract/pdf/`, `src/court_ocr_extract/pdf_render.py`
- Preprocess: `src/court_ocr_extract/preprocess.py`, `src/court_ocr_extract/image_processing/`
- Surya/OCR cache: `src/court_ocr_extract/ocr/`, `src/court_ocr_extract/ocr_backends/surya_ocr.py`, `src/court_ocr_extract/ocr_cache.py`
- Extraction orchestrator: canonical `src/court_ocr_extract/extraction_pipeline.py`.
- Extractor backends: canonical `src/court_ocr_extract/extractors/`; Local LLM backend ở `extractors/local_llm_extractor.py`, rule helper ở `extractors/rule_support.py`.
- Pre-content baseline: `extractors/pre_content_anchor_segmenter.py`, `extractors/rule_anchor_extractor.py`, `extractors/rule_anchor_strategies.py`; legacy hybrid/LLM-only modules chỉ phục vụ explicit comparison.
- Local LLM client/parser: `src/court_ocr_extract/local_llm/`.
- Typed merge/schema/validation compatibility: `src/court_ocr_extract/extraction/`; package này không còn sở hữu extractor backend.
- Validation/QA: `src/court_ocr_extract/validation.py`, `src/court_ocr_extract/extraction/validators.py`, `src/court_ocr_extract/qa.py`.
- Excel export: canonical `src/court_ocr_extract/excel_writer.py`; JSON helper vẫn ở `src/court_ocr_extract/export/json_writer.py`.
- Review UI/debug: `src/court_ocr_extract/visual_debug.py`, `src/court_ocr_extract/review_html.py`, `src/court_ocr_extract/extraction_preview.py`
- Ezycloudx/remote worker: `src/court_ocr_extract/remote_worker/`, `scripts/ezycloudx_*`
- Architecture audit/tooling: `scripts/repo_inventory.py`, `scripts/import_graph.py`, `scripts/check_architecture_guardrails.py`, `docs/REPO_INVENTORY.md`, `docs/IMPORT_GRAPH.md`, `docs/LEGACY_ARCHIVE_PLAN.md`

Phase 1D removed old UI app folders: `app/`, `app_fastapi/`, and `app_streamlit/`. The current supported operator surface is the CLI/debug-output path plus dedicated transfer/remote-worker tooling; restore old UI code from Git history only if explicitly needed.

Phase 1B/1E canonical decisions:

- Config: `src/court_ocr_extract/settings.py` is canonical for the rebuild.
- Compatibility config: `src/court_ocr_extract/config.py` remains for older imports and should not be expanded unless necessary.
- Excel writer: `src/court_ocr_extract/excel_writer.py` là canonical path duy nhất.
- Phase 1E đã migrate caller và xóa `src/court_ocr_extract/excel.py` cùng `src/court_ocr_extract/export/excel_writer.py`; restore bằng Git history trước Phase 1E nếu cần.

Phase 1F canonical decisions:

- Orchestrator: `src/court_ocr_extract/extraction_pipeline.py`.
- Backend interface/factory: `src/court_ocr_extract/extractors/base.py` và `extractors/__init__.py`.
- Local LLM: `src/court_ocr_extract/extractors/local_llm_extractor.py`.
- Rule support: `src/court_ocr_extract/extractors/rule_support.py` với parser nội bộ `extractors/rule_parser.py`.
- Typed old-pipeline behavior được giữ bằng `TypedLocalLLMExtractor` trong canonical module, không bằng duplicate module/wrapper.

Legacy or conflict candidates are tracked in `docs/CLEANUP_PLAN.md`.

## Proposed Post-Cleanup Structure

```text
src/court_ocr_extract/
  core/
  render/
  preprocess/
  ocr/
    surya/
    cache/
  vlm/
  extractors/
  validate/
  export/
  qa/
  review_ui/
  cli/

docs/
  PROJECT_STATE.md
  ARCHITECTURE.md
  DECISIONS.md
  AGENT_ROLES.md
  CLEANUP_PLAN.md
  PIPELINE_SPEC.md
  DEBUG_OUTPUT_SPEC.md

scripts/
  check_*.py
  run_*.ps1
  smoke_*.py
  benchmark_*.py
  guardrail_*.py
```

No files have been moved into this structure during Phase 1A.
