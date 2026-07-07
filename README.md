# Court OCR Extract

Pipeline xử lý PDF bản án/quyết định tòa án Việt Nam theo từng bước có thể kiểm tra bằng mắt:

```text
PDF -> render ảnh -> preprocess optional -> OCR cache -> marker detection
-> extraction preview -> Excel -> QA từ Excel
```

Deliverable cuối là file `.xlsx`. JSON chỉ là artifact debug khi bật `--debug-json`.

## Nguyên tắc vận hành

- Workflow kiểm chứng chất lượng phải dùng PDF thật do bạn trực tiếp upload/chạy trên VM hoặc máy nội bộ.
- Không dùng dữ liệu giả để kết luận chất lượng OCR/extraction. Unit test trong repo chỉ kiểm tra contract code, schema, control-flow.
- Codex không tự mở, đọc, OCR, parse hoặc in nội dung PDF thật/derived artifact thật trong quá trình sửa code.
- Không dùng Git để upload PDF thật.
- Không in full OCR text, tên người, địa chỉ, CCCD/CMND hoặc tên file PDF thật ra terminal.
- Không fallback âm thầm giữa OCR backend hoặc extractor.
- Cloud OCR/extraction tắt mặc định, chỉ chạy khi bật rõ trong `.env`.
- Không chạy full nếu real-data pilot 10/20 PDF thật chưa được mở visual QA, extraction preview và Excel để chấp nhận.

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
.\.venv\Scripts\python.exe -m pip install -e .
Copy-Item .env.example .env -Force
```

## Upload PDF Thật

```powershell
python -m scripts.transfer_server --host 127.0.0.1 --port 8765 --token <token-rieng>
cloudflared tunnel --url http://127.0.0.1:8765
```

Upload PDF/ZIP vào `data\raw_pdfs\uploads\`. Server chỉ cho download Excel và debug visual zip.

## Runtime Checks

```powershell
python -m scripts.check_runtime --ocr-backend tesseract --extractor local_llm
python -m scripts.check_ocr_backend --backend tesseract
python -m scripts.check_extractor --backend local_llm
```

## Synthetic Smoke Debug

This smoke command creates safe, non-real artifacts that a reviewer can open before any real-data pilot. It does not prove real-data OCR/extraction quality.

```powershell
python -m scripts.smoke_synthetic_debug
```

Outputs:

- `outputs\debug_visual\synthetic_smoke\index.html`
- `outputs\debug_visual\synthetic_smoke\manifest.json`
- `outputs\extraction_draft\synthetic_smoke\draft_internal.jsonl`
- `outputs\extraction_draft\synthetic_smoke\draft_summary.xlsx`
- `outputs\excel\synthetic_smoke.xlsx`
- `outputs\qa\synthetic_smoke_report.json`

After this passes, the next quality step is still the real-data pilot on VM with a real OCR backend.

## OCR Cache

```powershell
python -m court_ocr_extract.cli ocr --input-dir data\raw_pdfs\uploads --limit 10 --cache-dir outputs\ocr_cache --ocr-backend tesseract
```

Fallback chỉ chạy khi bật rõ:

```powershell
python -m court_ocr_extract.cli ocr --input-dir data\raw_pdfs\uploads --limit 10 --cache-dir outputs\ocr_cache --ocr-backend google_document_ai --fallback-ocr-backend tesseract
```

## Visual QA Từng Bước Trên PDF Thật

```powershell
python -m court_ocr_extract.cli debug-render --input data\raw_pdfs\uploads --limit 20 --review-sample-size 5 --pages 1-3 --output outputs\debug_visual --open
python -m court_ocr_extract.cli debug-preprocess --input data\raw_pdfs\uploads --limit 20 --review-sample-size 5 --pages 1-3 --output outputs\debug_visual --open
python -m court_ocr_extract.cli debug-red-seal --input data\raw_pdfs\uploads --limit 20 --review-sample-size 5 --pages 1-3 --output outputs\debug_visual --open
python -m court_ocr_extract.cli debug-ocr-review --input data\raw_pdfs\uploads --limit 20 --review-sample-size 5 --pages 1-3 --ocr-backend tesseract --output outputs\debug_visual --open
python -m court_ocr_extract.cli debug-marker --ocr-cache outputs\ocr_cache --review-sample-size 5 --review-mode mixed --output outputs\debug_visual --open
```

## Extraction Preview

```powershell
python -m court_ocr_extract.cli preview-extraction --ocr-cache outputs\ocr_cache --review-sample-size 5 --review-mode mixed --extractor local_llm --output outputs\debug_visual --open
```

## Excel Và QA

```powershell
python -m court_ocr_extract.cli extract --ocr-cache outputs\ocr_cache --output outputs\excel\pilot_10.xlsx --extractor local_llm
python -m scripts.qa_output --excel outputs\excel\pilot_10.xlsx
```

Excel có sheet `DATA` và `RUN_SUMMARY`.

## Benchmark Trên PDF Thật

```powershell
python -m court_ocr_extract.cli benchmark-ocr --input-dir data\raw_pdfs\uploads --limit 10 --backends google_document_ai,google_vision,openai_vision,gemini_document,tesseract --output outputs\excel\ocr_benchmark.xlsx --debug-visual --review-sample-size 5 --review-mode mixed
python -m court_ocr_extract.cli benchmark-extractors --ocr-cache outputs\ocr_cache --input-dir data\raw_pdfs\uploads --limit 10 --extractors local_llm,openai,gemini,direct_vision_openai,direct_vision_gemini --output outputs\excel\extractor_benchmark.xlsx --debug-visual --review-sample-size 5 --review-mode mixed
```

## Real-Data Pilot Và Full

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_sample_windows.ps1 -OcrBackend tesseract -Extractor local_llm -DebugVisual -ReviewSampleSize 5 -ReviewMode mixed
```

Chỉ sau khi bạn chấp nhận pilot PDF thật:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_full_windows.ps1 -OcrBackend tesseract -Extractor local_llm -ReviewSampleSize 10 -ReviewMode mixed -AcceptedSample10
```

## Zip Debug Visual

```powershell
python -m court_ocr_extract.cli zip-debug-visual --run-id latest --output outputs\debug_visual\latest_debug_visual.zip
```

## Cần Kiểm Tra Bằng Mắt

- Render đúng DPI, không xoay/cắt mép.
- Preprocess không làm mất chữ hoặc mất dấu tiếng Việt.
- Red seal removal chỉ bật khi xem nhiều PDF thật thấy an toàn.
- OCR review có text khớp ảnh.
- Marker `NỘI DUNG VỤ ÁN` được phát hiện hợp lý.
- Extraction preview bên trái đúng cột Excel, bên phải có evidence.
- Excel không bắt nhầm cụm trạng thái thành họ tên.
- QA không in dữ liệu nhạy cảm.

Không gọi trạng thái này là production-ready nếu pilot PDF thật chưa được bạn kiểm tra và chấp nhận.
