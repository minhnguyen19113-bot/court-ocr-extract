# Ezycloudx Windows VM Runbook

## 1. Cài Đặt

```powershell
winget install --id Git.Git -e
winget install --id Python.Python.3.11 -e
winget install --id Microsoft.VisualStudioCode -e
winget install --id Ollama.Ollama -e
```

```powershell
cd C:\
git clone https://github.com/<user>/<repo>.git court-ocr-extract
cd C:\court-ocr-extract
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
Copy-Item .env.example .env -Force
```

## 2. Upload PDF Thật

Không upload PDF thật bằng Git hoặc RDP clipboard làm workflow chính.

```powershell
python -m scripts.transfer_server --host 127.0.0.1 --port 8765 --token <token-rieng>
cloudflared tunnel --url http://127.0.0.1:8765
```

Cloudflare quick tunnel là link tạm thời. Upload PDF hoặc ZIP vào `data\raw_pdfs\uploads\`.

## 3. Check Runtime

```powershell
python -m scripts.check_runtime --ocr-backend tesseract --extractor local_llm
python -m scripts.check_ocr_backend --backend tesseract
python -m scripts.check_extractor --backend local_llm
```

## 4. Real-Data Pilot 10/20

Không dùng dữ liệu giả để đánh giá chất lượng. Pilot phải chạy trên PDF thật mà bạn upload.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_sample_windows.ps1 -OcrBackend tesseract -Extractor local_llm -DebugVisual -ReviewSampleSize 5 -ReviewMode mixed
```

Mở:

- `outputs\debug_visual\...\index.html`
- `outputs\debug_visual\...\extraction_preview\index.html`
- `outputs\excel\pilot_10.xlsx` hoặc `outputs\excel\sample_10.xlsx`

Sau đó chạy:

```powershell
python -m scripts.qa_output --excel outputs\excel\pilot_10.xlsx
```

## 5. Full Run

Không chạy full nếu real-data pilot chưa đạt.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_full_windows.ps1 -OcrBackend tesseract -Extractor local_llm -ReviewSampleSize 10 -ReviewMode mixed -AcceptedSample10
```

## 6. Download Output

```powershell
python -m court_ocr_extract.cli zip-debug-visual --run-id latest --output outputs\debug_visual\latest_debug_visual.zip
```

Mở transfer server và tải Excel/debug zip. Server không cho download raw/private PDF.
