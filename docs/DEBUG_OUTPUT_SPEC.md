# Debug Output Spec

Last updated: 2026-07-07

Debug output is mandatory for reviewer trust. It must be safe by default and should never print or expose full real OCR text in logs.

## Output Layout

Target synthetic-safe layout pattern:

```text
outputs/debug_visual/<run_id>/
  index.html
  manifest.json
  cases/
    <case_id>/
      render.html
      preprocess.html
      ocr.html
      extraction.html
      qa.html
```

Codex must not inspect real folders under `outputs/`. This layout is a target spec only.

## Index Page

Must show:

- run metadata
- case list
- step status
- rows needing review
- warning counts
- links to per-case pages

## Render View

Must show:

- page grid
- rendered page image
- page size/DPI
- warnings for blank, rotated, cropped, or unreadable pages

## Preprocess View

Must show:

- before/after images side by side
- transform list
- non-overwrite guarantee
- warnings for risky transforms

## OCR View

Must show:

- original image
- bbox overlay
- line table with `line_id`, bbox, reading order, text, confidence, warnings
- low-confidence filter

## VLM View

Must show:

- page image
- model output
- parsed JSON status
- extracted fields
- evidence and hallucination warnings

## Extraction View

Must show:

- field/value/evidence table
- source page and line IDs
- warning code
- link to OCR line or bbox when available

## QA View

Must show:

- row count
- needs-review count
- missing evidence
- evidence mismatch
- invalid date/ID
- low OCR confidence
- duplicate participant warnings

## Privacy

- Do not include full real OCR text in terminal logs.
- Do not include sensitive filenames in logs.
- Debug outputs from real data are derived sensitive artifacts and must stay out of Git.
