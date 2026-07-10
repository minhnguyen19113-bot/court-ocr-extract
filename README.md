# Court OCR Extract

This repo is in rebuild. It targets step-by-step extraction from Vietnamese court PDFs with mandatory visual QA before any Excel output is trusted.

## Current Direction

Main candidate:

```text
PDF -> render page image -> optional preprocess/enhance -> Surya OCR
-> OCRCacheRecord/text cache -> normalize/split -> rule extraction
-> local LLM extraction -> evidence validation -> Excel -> QA report
-> debug UI/human review
```

Benchmark path:

```text
PDF/page image -> local VLM direct extraction -> validation
-> Excel -> QA report -> debug UI/human review
```

Tesseract is legacy optional only, not the main/default path. PaddleOCR is not used. Cloud OpenAI/Google/Gemini adapters are disabled by default and are opt-in benchmark paths only.

Synthetic smoke checks are contract/control-flow checks. They do not prove real OCR or extraction quality.

## Operating Rules

- The Project Owner runs real-data pilots on Ezycloudx or a local controlled machine.
- Codex must not open, OCR, parse, summarize, or quote real PDFs or real derived artifacts.
- Do not upload real PDFs or derived outputs through Git.
- Do not print full OCR text, names, addresses, ID numbers, or sensitive filenames in logs.
- Do not silently fallback between OCR backends or extractor backends.
- Do not run full production batches until a real-data pilot has been visually reviewed and accepted.

## Setup Windows VM

```powershell
winget install --id Git.Git -e
winget install --id Python.Python.3.11 -e
winget install --id Microsoft.VisualStudioCode -e
winget install --id Ollama.Ollama -e

cd C:\
git clone https://github.com/<user>/<repo>.git court-ocr-extract
cd C:\court-ocr-extract
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev,ocr]"
Copy-Item .env.example .env -Force
```

## Transfer Server

```powershell
python -m scripts.transfer_server --host 127.0.0.1 --port 8765 --token <private-token>
cloudflared tunnel --url http://127.0.0.1:8765
```

Upload real PDF/ZIP files to `data\raw_pdfs\uploads\` on the VM. The transfer server is for user-controlled runtime only.

## Runtime Checks

Target Surya + local LLM checks:

```powershell
python -m scripts.check_runtime --ocr-backend surya --extractor local_llm
python -m scripts.check_ocr_backend --backend surya
python -m scripts.check_extractor --backend local_llm
```

The main adapter is pinned to `surya-ocr==0.20.0`. `surya-ocr>=0.21.0` is Surya 2 and is not supported by this path; the availability check fails before Docker/vLLM runtime. Reinstall from `.[dev,ocr]` after pulling dependency changes, and do not replace the pin with an unversioned install.

## Synthetic Smoke Debug

This command creates safe, non-real artifacts that a reviewer can open before any real-data pilot. It does not prove real-data quality.

```powershell
python -m scripts.smoke_synthetic_debug
```

Expected synthetic outputs:

- `outputs\debug_visual\synthetic_smoke\index.html`
- `outputs\debug_visual\synthetic_smoke\manifest.json`
- `outputs\extraction_draft\synthetic_smoke\draft_internal.jsonl`
- `outputs\extraction_draft\synthetic_smoke\draft_summary.xlsx`
- `outputs\excel\synthetic_smoke.xlsx`
- `outputs\qa\synthetic_smoke_report.json`

## Synthetic Evaluation Toolkit

Validate and evaluate only the committed redacted fixtures:

```powershell
python -m scripts.check_gold_manifest --gold tests\fixtures\gold_manifest_synthetic.jsonl
python -m scripts.evaluate_gold_manifest --gold tests\fixtures\gold_manifest_synthetic.jsonl --predictions tests\fixtures\prediction_manifest_synthetic.jsonl
```

Real gold/prediction manifests stay outside Git and Codex. Evaluation output contains aggregate metrics only and does not replace human review.

## Target OCR Cache

Target command for the Surya path:

```powershell
python -m court_ocr_extract.cli ocr --input-dir data\raw_pdfs\uploads --limit 10 --cache-dir outputs\ocr_cache --ocr-backend surya
```

Fallbacks must be explicit and visible in logs/debug output. Cloud fallbacks are opt-in benchmark work only.

## Target Visual QA

```powershell
python -m court_ocr_extract.cli debug-render --input data\raw_pdfs\uploads --limit 20 --review-sample-size 5 --pages 1-3 --output outputs\debug_visual --open
python -m court_ocr_extract.cli debug-preprocess --input data\raw_pdfs\uploads --limit 20 --review-sample-size 5 --pages 1-3 --output outputs\debug_visual --open
python -m court_ocr_extract.cli debug-ocr-review --input data\raw_pdfs\uploads --limit 20 --review-sample-size 5 --pages 1-3 --ocr-backend surya --output outputs\debug_visual --open
```

Required review views:

- render grid and page metadata
- preprocess before/after
- Surya bbox overlay and OCR line text
- low-confidence lines
- extraction evidence
- evidence mismatch warnings
- Excel and QA summary

## Extraction Preview, Excel, QA

```powershell
python -m court_ocr_extract.cli preview-extraction --ocr-cache outputs\ocr_cache --review-sample-size 5 --review-mode mixed --extractor local_llm --output outputs\debug_visual --open
python -m court_ocr_extract.cli extract --ocr-cache outputs\ocr_cache --output outputs\excel\pilot_10.xlsx --extractor local_llm
python -m scripts.qa_output --excel outputs\excel\pilot_10.xlsx
```

Excel output should include or prepare for source/evidence columns such as `SOURCE_CASE_ID`, `SOURCE_PAGE`, `SOURCE_LINE_IDS`, `OCR_CONFIDENCE`, `EVIDENCE`, `WARNINGS`, and `NEEDS_REVIEW`.

## Real-Data Pilot And Full Run

Target pilot command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_sample_windows.ps1 -OcrBackend surya -Extractor local_llm -DebugVisual -ReviewSampleSize 5 -ReviewMode mixed
```

Target full-run command after the Project Owner accepts the pilot:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_full_windows.ps1 -OcrBackend surya -Extractor local_llm -ReviewSampleSize 10 -ReviewMode mixed -AcceptedSample10
```

The VLM benchmark path is separate and must produce comparable validation, QA, and debug output before it can be compared fairly with the Surya path.

## Zip Debug Visual

```powershell
python -m court_ocr_extract.cli zip-debug-visual --run-id latest --output outputs\debug_visual\latest_debug_visual.zip
```

## Manual Acceptance Checklist

- Render is correct DPI, not rotated, and not cropped.
- Preprocess does not remove text or Vietnamese marks.
- Surya OCR text matches page images and bbox overlays.
- Marker detection is reasonable.
- Extraction preview matches Excel columns and shows evidence.
- Excel does not mistake status phrases for names.
- QA report does not expose sensitive data.

Do not call the pipeline production-ready until the Project Owner has reviewed and accepted real-data pilot outputs.
