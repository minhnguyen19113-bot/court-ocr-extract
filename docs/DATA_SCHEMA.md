# Data Schema

Last updated: 2026-07-07

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
