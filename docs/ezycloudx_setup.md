# Ezycloudx Setup

This short setup note is superseded by `docs/ezycloudx_runbook.md` and `docs/RUNBOOK_EZYCLOUDX.md`.

## Base Setup

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

## Transfer Server

```powershell
python -m scripts.transfer_server --host 127.0.0.1 --port 8765 --token <private-token>
cloudflared tunnel --url http://127.0.0.1:8765
```

## Target Pilot

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_sample_windows.ps1 -OcrBackend surya -Extractor local_llm -DebugVisual -ReviewSampleSize 5 -ReviewMode mixed
```

Surya is the main target backend. Runtime wiring/import may still need Phase 2 setup on the VM.

Do not use fake data to decide OCR/extraction quality. The Project Owner runs and reviews real-data pilots outside Codex.
