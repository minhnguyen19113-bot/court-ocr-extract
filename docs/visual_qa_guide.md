# Visual QA Guide

Visual QA is mandatory before trusting Excel output. Synthetic fixtures can prove contracts and artifact generation only; they cannot prove real OCR/extraction quality.

## Synthetic Smoke Output

```powershell
python -m scripts.smoke_synthetic_debug
```

Safe synthetic outputs:

- `outputs\debug_visual\synthetic_smoke\index.html`
- `outputs\debug_visual\synthetic_smoke\manifest.json`
- `outputs\excel\synthetic_smoke.xlsx`
- `outputs\qa\synthetic_smoke_report.json`

## Render Review

Check page grid, page size, DPI, rotation, blank pages, and cropped edges.

```powershell
python -m court_ocr_extract.cli debug-render --input data\raw_pdfs\uploads --limit 20 --review-sample-size 5 --output outputs\debug_visual --open
```

By default this renders all pages. Use `--pages 1-3` only when a bounded page sample is intentional.

## Preprocess Review

Compare before/after side by side. Do not enable aggressive enhancement if it removes text strokes or Vietnamese marks.

```powershell
python -m court_ocr_extract.cli debug-preprocess --input data\raw_pdfs\uploads --limit 20 --review-sample-size 5 --output outputs\debug_visual --open
```

By default this preprocesses all rendered pages. Use `--pages 1-3` only when a bounded page sample is intentional.

## Surya OCR Review

Target review command:

```powershell
python -m court_ocr_extract.cli debug-ocr-review --input data\raw_pdfs\uploads --limit 20 --review-sample-size 5 --ocr-backend surya --full-document --output outputs\debug_visual --open
```

Use `--full-document` for whole-PDF OCR review so the content marker does not stop or truncate the review.

Required review elements:

- original page image
- bbox overlay
- line IDs
- bbox coordinates
- OCR text per line
- reading order
- confidence if available
- low-confidence filter

If bbox/confidence is missing, the UI must say so clearly instead of inventing values.

## VLM Benchmark Review

The VLM benchmark view must show page image, model output, parsed JSON status, extracted fields, evidence, and hallucination/evidence warnings.

## Extraction Review

```powershell
python -m court_ocr_extract.cli preview-extraction --ocr-cache outputs\ocr_cache --review-sample-size 5 --review-mode mixed --extractor local_llm --output outputs\debug_visual --open
```

Review every field/value with evidence, source page, source line IDs, warning codes, and links back to OCR lines/bboxes when available.

## Excel / QA Review

Check:

- total rows
- rows needing review
- invalid date or ID
- missing evidence
- evidence mismatch
- low OCR confidence
- duplicate participant warnings

QA and logs must not expose full OCR text or sensitive personal data.
