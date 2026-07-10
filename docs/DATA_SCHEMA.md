# Data Schema

Last updated: 2026-07-10

This document records target schema expectations for rebuild planning. It does not change runtime behavior.

## OCR Cache Record

Required fields:

- `case_id`
- `source_ref` or redacted source identifier
- `backend`
- `pages`
- `created_at`
- `warnings`
- `metadata`

## OCR Page

Required fields:

- `page_number`
- `text`
- `lines`
- `width`
- `height`
- `dpi`
- `warnings`

## OCR Line

Required fields:

- `line_id`
- `page_number`
- `text`
- `bbox`
- `reading_order`
- `confidence`
- `warnings`

`bbox` should use a consistent shape such as `[x0, y0, x1, y1]` in image pixel coordinates.

## Extracted Field

Required fields:

- `name`
- `value`
- `evidence`
- `source_page`
- `source_line_ids`
- `confidence`
- `warnings`
- `needs_review`

Every non-null value must have evidence unless a reviewer-approved rule says otherwise.

## Participant Row

Target Excel/export row metadata:

- `SOURCE_CASE_ID`
- `SOURCE_PAGE`
- `SOURCE_LINE_IDS`
- `OCR_CONFIDENCE`
- `EXTRACTION_CONFIDENCE`
- `EVIDENCE`
- `WARNINGS`
- `NEEDS_REVIEW`

Domain fields should remain defined in `config/fields.yaml` or the canonical schema chosen in Phase 1B.

Phase 1E giữ nguyên workbook contract hiện tại của canonical `src/court_ocr_extract/excel_writer.py`:

- Draft-record API `write_excel()` tạo sheet `DATA` và `RUN_SUMMARY`.
- Typed-result API `write_excel_from_results()` tạo sheet `Trich xuat` để giữ tương thích hành vi của caller đã migrate.
- Cả hai API dùng cùng 11 domain headers trong `EXCEL_HEADERS`.

Các cột audit/trace mục tiêu bên trên chưa có trong 11 headers hiện tại:

- `SOURCE_CASE_ID`
- `SOURCE_PAGE`
- `SOURCE_LINE_IDS`
- `OCR_CONFIDENCE`
- `EXTRACTION_CONFIDENCE`
- `EVIDENCE`
- `WARNINGS`
- `NEEDS_REVIEW`

Phase 1E không ép thay đổi schema lớn. Việc bổ sung các cột này cần một phase schema riêng với migration/QA rõ ràng.

## Extraction Draft Contract

Canonical `extraction_pipeline.py` tạo draft envelope gồm:

- `case_id`
- `source_index`
- `ocr_backend`
- `extractor_backend`
- `marker_found`
- `status`
- `error`
- `payload`

`payload` hiện gồm `case`, `participants`, và `document_warnings`. Participant có `confidence`, `evidence`, và `warnings`; `needs_review` được tính bằng validation/review helper, chưa phải field persisted trực tiếp trong extraction payload. Phase 1F chỉ hợp nhất module, không đổi schema này.

## QA Report

Required metrics:

- `total_rows`
- `rows_need_review`
- `invalid_date_count`
- `invalid_id_count`
- `missing_evidence_count`
- `evidence_mismatch_count`
- `low_ocr_confidence_count`
- `duplicate_participant_count`
- `warning_counts`

The report must not include full real OCR text or unnecessary PII.

## Evaluation Manifests

Gold JSONL record:

- Safe IDs: `case_id_hash`, `file_hash`.
- Document labels: page count, tags, expected section presence/page.
- Field labels: redacted/hash value, source page/line IDs, redacted evidence, required flag.
- Participant labels: role, `name_hash`, redacted fields, source references.
- Human review status.

Prediction JSONL record:

- Run/backend/model/prompt versions.
- OCR aggregate counts.
- Predicted sections/fields/participants with evidence/source references.
- warnings và `needs_review`.

Evaluation report schema là whitelist numeric metrics trong `evaluation.metrics.METRIC_KEYS`; không chứa raw manifest values.
