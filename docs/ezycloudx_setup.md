# Ezycloudx Setup

This document is superseded by `docs/ezycloudx_runbook.md`.

Key rule: run quality validation on real court PDFs uploaded by the user. Do not use fake data to decide OCR/extraction quality.

Use:

```powershell
python -m scripts.transfer_server --host 127.0.0.1 --port 8765 --token <token-rieng>
cloudflared tunnel --url http://127.0.0.1:8765
```

Then run the real-data pilot:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_sample_windows.ps1 -OcrBackend tesseract -Extractor local_llm -DebugVisual -ReviewSampleSize 5 -ReviewMode mixed
```
