# Ezycloudx Runbook

Last updated: 2026-07-07

Đây là target rebuild runbook sau Phase 1B default cleanup và Phase 2A Surya adapter fix.

## Safety

- Do not upload real data through Git.
- Keep real PDFs and derived outputs on the VM or user-controlled storage.
- Treat rendered images, OCR cache, extraction drafts, Excel files, and debug UI as sensitive derived artifacts.
- Cloud APIs are disabled by default.

## Runtime Checks To Keep

The runbook should include checks for:

- Python environment.
- GPU availability.
- CUDA/torch compatibility.
- Surya install/import.
- vLLM or Ollama local endpoint.
- Local Qwen model availability.
- Disk space for rendered images and debug artifacts.
- Transfer server bound to safe interface.

## Pilot Workflow Gate

The Project Owner runs real-data pilot/full workflows outside Codex. Codex can write commands and scripts, but must not execute real-data OCR or inspect real outputs.

## Target Commands

Surya + local LLM target checks:

```powershell
python -m scripts.check_runtime --ocr-backend surya --extractor local_llm
.\.venv\Scripts\python -m scripts.check_ocr_backend --backend surya
python -m scripts.check_extractor --backend local_llm
```

## Pilot 1 PDF Full-Document Review

Project Owner đặt đúng 1 PDF cần pilot vào folder `data\raw_pdfs\pilot_one`. Các command debug/render/preprocess mặc định chạy toàn bộ trang nếu không truyền `--pages`; muốn giới hạn thì truyền rõ `--pages 1-3`.

```powershell
.\.venv\Scripts\python.exe -m court_ocr_extract.cli debug-render `
  --input data\raw_pdfs\pilot_one `
  --limit 1 `
  --review-sample-size 1 `
  --output outputs\debug_visual `
  --open
```

```powershell
.\.venv\Scripts\python.exe -m court_ocr_extract.cli debug-preprocess `
  --input data\raw_pdfs\pilot_one `
  --limit 1 `
  --review-sample-size 1 `
  --deskew off `
  --red-seal-removal on `
  --red-removal-mode neutralize `
  --text-enhance light `
  --preprocess-profile conservative `
  --output outputs\debug_visual_preprocess_v2 `
  --open
```

Project Owner phải kiểm tra original/red mask/black-text protection/seal removed/text enhanced/final và warnings của toàn bộ trang trước OCR. Nếu `neutralize` còn red residual, so sánh với `inpaint`:

```powershell
.\.venv\Scripts\python.exe -m court_ocr_extract.cli debug-preprocess `
  --input data\raw_pdfs\pilot_one `
  --limit 1 `
  --review-sample-size 1 `
  --deskew off `
  --red-seal-removal on `
  --red-removal-mode inpaint `
  --text-enhance light `
  --preprocess-profile conservative `
  --output outputs\debug_visual_preprocess_inpaint `
  --open
```

Nếu chữ vẫn mờ sau khi seal đã sạch, thử text medium riêng:

```powershell
.\.venv\Scripts\python.exe -m court_ocr_extract.cli debug-preprocess `
  --input data\raw_pdfs\pilot_one `
  --limit 1 `
  --review-sample-size 1 `
  --deskew off `
  --red-seal-removal on `
  --red-removal-mode inpaint `
  --text-enhance medium `
  --preprocess-profile balanced `
  --output outputs\debug_visual_preprocess_medium `
  --open
```

`white_fill`, `text-enhance=strong`, và `deskew=force` chỉ dùng thử nghiệm có visual review; không dùng làm default production.

OCR review toàn bộ file phải dùng `--full-document` để không cắt theo `settings.max_pages_before_marker` và không dừng/truncate tại marker nội dung.

```powershell
.\.venv\Scripts\python.exe -m court_ocr_extract.cli debug-ocr-review `
  --input data\raw_pdfs\pilot_one `
  --limit 1 `
  --review-sample-size 1 `
  --ocr-backend surya `
  --full-document `
  --output outputs\debug_visual `
  --open
```

OCR cache toàn bộ file cũng dùng `--full-document`; command này không chạy extraction/LLM/Excel.

```powershell
.\.venv\Scripts\python.exe -m court_ocr_extract.cli ocr `
  --input-dir data\raw_pdfs\pilot_one `
  --limit 1 `
  --cache-dir outputs\ocr_cache `
  --ocr-backend surya `
  --full-document `
  --debug-visual
```

Nếu thiếu Surya:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[ocr]"
# or
.\.venv\Scripts\python.exe -m pip install surya-ocr
```

Command target để review OCR:

```powershell
python -m court_ocr_extract.cli debug-ocr-review --input data\raw_pdfs\uploads --limit 5 --review-sample-size 5 --ocr-backend surya --full-document --output outputs\debug_visual --open
```

Project Owner chạy command này trên Ezycloudx với PDF thật. Codex không được chạy hoặc inspect real-data outputs.

Target pilot:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_sample_windows.ps1 -OcrBackend surya -Extractor local_llm -DebugVisual -ReviewSampleSize 5 -ReviewMode mixed
```

Target full run after Project Owner acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_full_windows.ps1 -OcrBackend surya -Extractor local_llm -ReviewSampleSize 10 -ReviewMode mixed -AcceptedSample10
```

Phase 2A đã wire `SuryaOCRBackend` cho API `surya-ocr 0.20.0` qua `RecognitionPredictor(..., full_page=True)`. Nếu `check_ocr_backend --backend surya` báo unsupported API, giữ nguyên default Surya và cập nhật adapter/version pin; không fallback sang Tesseract.

## VLM Benchmark

The VLM benchmark path must stay separate until it produces comparable validation, QA, and debug output. Treat VLM commands as target/planned unless the VM runtime has been explicitly checked.

## Troubleshooting Topics

- Surya runtime/model load failure.
- Local LLM endpoint unavailable.
- Strict JSON parsing failure.
- Evidence mismatch.
- Low OCR confidence.
- Debug UI artifact missing.
- Transfer server exposure and cleanup.
