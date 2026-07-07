# Ezycloudx Runbook

Last updated: 2026-07-07

This is the target rebuild runbook after Phase 1B default cleanup.

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
python -m scripts.check_ocr_backend --backend surya
python -m scripts.check_extractor --backend local_llm
```

Nếu thiếu Surya:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[ocr]"
# or
.\.venv\Scripts\python.exe -m pip install surya-ocr
```

Command target để review OCR:

```powershell
python -m court_ocr_extract.cli debug-ocr-review --input data\raw_pdfs\uploads --limit 5 --review-sample-size 5 --pages 1-3 --ocr-backend surya --output outputs\debug_visual --open
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

Surya runtime wiring/import may still need Phase 2 setup on the VM.

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
