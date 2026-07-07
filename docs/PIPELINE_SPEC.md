# Pipeline Spec

Last updated: 2026-07-07

This is the target rebuild spec. Phase 1B cleaned defaults to match this spec but did not implement real runtime changes.

## Render

Terminal summary must include:

- `case_id`
- page count
- DPI
- output paths
- warnings for blank, rotated, or cropped pages

Debug UI must include:

- page render grid
- page image
- page size/DPI metadata

## Preprocess / Enhance

Terminal summary must include:

- before image path
- after image path
- transforms applied
- warnings when transforms may remove text or accents

Debug UI must include:

- before/after side-by-side
- clear indication that original images are not overwritten

## Surya OCR

Terminal summary must include:

- pages processed
- total OCR lines
- low-confidence line count
- bbox overlay output path
- OCR cache output path
- short safe preview only; never full real OCR text

Debug UI must include:

- original page image
- bbox overlay image
- `line_id`
- bbox
- per-line text
- confidence if available
- reading order
- low-confidence filter

## VLM End-to-End

Terminal summary must include:

- pages processed
- model name
- JSON valid yes/no
- extraction warnings
- debug output path
- no full PII

Debug UI must include:

- page image
- VLM output
- extracted fields
- evidence
- warning and hallucination checks

## Extraction

Terminal summary must include:

- JSON valid status
- participant/row count
- missing evidence count
- evidence mismatch count
- rows needing review
- output paths

Debug UI must include:

- field/value table
- evidence
- source page/line
- warning code
- link to bbox/page when available

## Excel / QA

Terminal summary must include:

- total rows
- rows needing review
- invalid dates/IDs
- missing evidence count
- evidence mismatch count
- low OCR confidence count
- output Excel path
- output QA report path

Excel should include or prepare for:

- `SOURCE_CASE_ID`
- `SOURCE_PAGE`
- `SOURCE_LINE_IDS`
- `OCR_CONFIDENCE`
- `EXTRACTION_CONFIDENCE`
- `EVIDENCE`
- `WARNINGS`
- `NEEDS_REVIEW`

## Fallback Rules

- No silent OCR fallback.
- No silent extractor fallback.
- Fallbacks must be explicit, logged, and visible in QA/debug output.
