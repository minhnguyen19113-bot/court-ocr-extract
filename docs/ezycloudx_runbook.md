# Ezycloudx Windows VM Runbook

This runbook reflects Phase 1B defaults. Surya OCR + local LLM is the main candidate. Local VLM is a benchmark path. Tesseract is legacy optional only.

## 1. Base Setup

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

Optional GPU/runtime checks:

```powershell
nvidia-smi
.\.venv\Scripts\python.exe -m pip install -e .[ocr,gpu]
```

## 2. Transfer Server

Do not upload real PDFs through Git.

```powershell
python -m scripts.transfer_server --host 127.0.0.1 --port 8765 --token <private-token>
cloudflared tunnel --url http://127.0.0.1:8765
```

Upload real PDF/ZIP files to `data\raw_pdfs\uploads\` on the VM.

## 3. Target Runtime Checks

Surya + local LLM target:

```powershell
python -m scripts.check_runtime --ocr-backend surya --extractor local_llm
python -m scripts.check_ocr_backend --backend surya
python -m scripts.check_extractor --backend local_llm
```

Local LLM target:

```powershell
# vLLM/OpenAI-compatible local endpoint target
# LOCAL_LLM_PROVIDER=vllm
# LOCAL_LLM_MODEL_NAME=Qwen/Qwen2.5-14B-Instruct
# LOCAL_LLM_BASE_URL=http://127.0.0.1:8001/v1
```

VLM benchmark target:

```powershell
python -m scripts.check_vlm_backend
```

Surya runtime wiring/import may still need Phase 2 setup. If Surya is unavailable, record the failure and fix runtime setup rather than changing the main default.

## 4. Real-Data Pilot

Do not use synthetic fixtures to judge quality. The Project Owner must visually review real-data outputs.

Target Surya pilot:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_sample_windows.ps1 -OcrBackend surya -Extractor local_llm -DebugVisual -ReviewSampleSize 5 -ReviewMode mixed
```

Open and review:

- render review
- preprocess before/after
- OCR bbox/text review
- extraction preview
- `outputs\excel\pilot_10.xlsx`
- QA report
- debug visual zip

## 5. VLM Benchmark Pilot

The VLM path must produce comparable validation, QA, and debug output before comparison with the Surya path. Treat VLM commands as target/planned unless the VLM runtime has been wired and checked on the VM.

## 6. Full Run Gate

Do not run full batches until the real-data pilot passes review.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_full_windows.ps1 -OcrBackend surya -Extractor local_llm -ReviewSampleSize 10 -ReviewMode mixed -AcceptedSample10
```

## 7. Download Output

```powershell
python -m court_ocr_extract.cli zip-debug-visual --run-id latest --output outputs\debug_visual\latest_debug_visual.zip
```

The transfer server must not expose raw/private PDFs.
