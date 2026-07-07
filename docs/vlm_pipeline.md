# VLM Pipeline

This project can add a local VLM page reader without using Tesseract or cloud OCR APIs.

## Flow

```text
PDF -> render page images -> local VLM reads each page -> OCR-compatible cache
-> LocalLLMExtractor -> validation -> Excel -> debug UI
```

The minimal bridge writes VLM output into the existing `OCRCacheRecord` / `OCRResult` shape, so extraction, Excel, QA, and preview code can stay mostly unchanged.

## Fake Smoke

Run this first. It does not use real PDFs or a real VLM model.

```powershell
python -m scripts.check_vlm_backend
python -m scripts.smoke_vlm_synthetic
```

Open:

- `outputs\debug_visual\vlm_synthetic_smoke\index.html`
- `outputs\debug_visual\vlm_synthetic_smoke\manifest.json`
- `outputs\debug_visual\vlm_synthetic_smoke\page_001.md`
- `outputs\debug_visual\vlm_synthetic_smoke\combined_vlm_text.md`

Synthetic smoke only proves the VLM cache/debug contract. It does not prove quality on real court PDFs.

## Ollama VLM Smoke

Verify the actual Ollama tag on your machine:

```powershell
ollama list
ollama pull qwen2.5vl:3b
```

Example env:

```env
VLM_PROVIDER=ollama
VLM_MODEL_NAME=qwen2.5vl:3b
VLM_BASE_URL=http://127.0.0.1:11434
VLM_TEMPERATURE=0
VLM_TIMEOUT_SECONDS=300
VLM_RENDER_DPI=200
VLM_MAX_PAGES=0
```

Baseline:

```env
VLM_PROVIDER=ollama
VLM_MODEL_NAME=qwen2.5vl:7b
VLM_BASE_URL=http://127.0.0.1:11434
VLM_TEMPERATURE=0
VLM_TIMEOUT_SECONDS=600
VLM_RENDER_DPI=200
VLM_MAX_PAGES=0
```

## Review Guidance

For each case, review the page image beside the VLM markdown text before trusting the Excel output. Watch for:

- skipped lines
- invented names, dates, IDs, or addresses
- `[KHONG DOC DUOC]` / `[KHÔNG ĐỌC ĐƯỢC]` markers
- evidence that does not appear in the VLM text

Do not paste real PDF text, OCR/VLM text, names, addresses, CCCD/CMND, or sensitive file names into cloud tools.

## Real PDF Pilot

After synthetic smoke passes:

1. Try 5 real PDFs locally.
2. Review every rendered image and VLM text page.
3. Move to 10 PDFs only if the first pass is understandable.
4. Use 30 PDFs to find repeated layout/model failures.
5. Benchmark 50-100 PDFs before choosing `qwen2.5vl:3b` or `qwen2.5vl:7b`.

