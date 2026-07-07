param(
  # tesseract is legacy only; not the main/default path.
  [ValidateSet("surya", "vlm", "tesseract")]
  [string]$OcrBackend = "surya",
  [string]$Extractor = "local_llm",
  [int]$ReviewSampleSize = 10,
  [string]$ReviewMode = "mixed",
  [switch]$DebugVisualAll,
  [switch]$AcceptedSample10
)

$ErrorActionPreference = "Stop"
if (-not $AcceptedSample10) {
  throw "Full run is blocked until the real-data pilot is reviewed and accepted. Re-run with -AcceptedSample10 after review."
}

$Python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { $Python = "python" }

if ($OcrBackend -eq "vlm") {
  Write-Warning "The VLM benchmark path does not use this OCR-cache full-run script yet. Use documented VLM target/planned commands after VLM validation parity is wired."
  throw "VLM benchmark path is not wired into run_full_windows.ps1."
}

if ($OcrBackend -eq "surya") {
  Write-Warning "Surya is the main target backend, but runtime wiring/import may still need Phase 2 setup on this VM."
}

& $Python -m scripts.check_runtime --ocr-backend $OcrBackend --extractor $Extractor

$ocrArgs = @("-m", "court_ocr_extract.cli", "ocr", "--input-dir", "data\raw_pdfs\uploads", "--cache-dir", "outputs\ocr_cache", "--ocr-backend", $OcrBackend)
if ($DebugVisualAll) { $ocrArgs += "--debug-visual" }
& $Python @ocrArgs

& $Python -m court_ocr_extract.cli preview-extraction --ocr-cache outputs\ocr_cache --review-sample-size $ReviewSampleSize --review-mode $ReviewMode --extractor $Extractor --output outputs\debug_visual
& $Python -m court_ocr_extract.cli extract --ocr-cache outputs\ocr_cache --output outputs\excel\full_run.xlsx --extractor $Extractor --review-sample-size $ReviewSampleSize --review-mode $ReviewMode
& $Python -m scripts.qa_output --excel outputs\excel\full_run.xlsx

Write-Host "Full run finished"
Write-Host "Excel: outputs\excel\full_run.xlsx"
