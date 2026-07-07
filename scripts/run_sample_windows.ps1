param(
  [string]$OcrBackend = "tesseract",
  [string]$Extractor = "local_llm",
  [switch]$DebugVisual,
  [int]$ReviewSampleSize = 5,
  [string]$ReviewMode = "mixed"
)

$ErrorActionPreference = "Stop"
$Python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { $Python = "python" }

& $Python -m scripts.check_runtime --ocr-backend $OcrBackend --extractor $Extractor
& $Python -m scripts.check_ocr_backend --backend $OcrBackend
& $Python -m scripts.check_extractor --backend $Extractor

$ocrArgs = @("-m", "court_ocr_extract.cli", "ocr", "--input-dir", "data\raw_pdfs\uploads", "--limit", "10", "--cache-dir", "outputs\ocr_cache", "--ocr-backend", $OcrBackend)
if ($DebugVisual) { $ocrArgs += "--debug-visual" }
& $Python @ocrArgs

if ($DebugVisual) {
  & $Python -m court_ocr_extract.cli debug-render --input data\raw_pdfs\uploads --limit 10 --review-sample-size $ReviewSampleSize --review-mode $ReviewMode --output outputs\debug_visual
  & $Python -m court_ocr_extract.cli debug-preprocess --input data\raw_pdfs\uploads --limit 10 --review-sample-size $ReviewSampleSize --review-mode $ReviewMode --output outputs\debug_visual
  & $Python -m court_ocr_extract.cli debug-ocr-review --input data\raw_pdfs\uploads --limit 10 --review-sample-size $ReviewSampleSize --review-mode $ReviewMode --ocr-backend $OcrBackend --output outputs\debug_visual
}

& $Python -m court_ocr_extract.cli preview-extraction --ocr-cache outputs\ocr_cache --review-sample-size $ReviewSampleSize --review-mode $ReviewMode --extractor $Extractor --output outputs\debug_visual
& $Python -m court_ocr_extract.cli extract --ocr-cache outputs\ocr_cache --output outputs\excel\pilot_10.xlsx --extractor $Extractor --review-sample-size $ReviewSampleSize --review-mode $ReviewMode
& $Python -m scripts.qa_output --excel outputs\excel\pilot_10.xlsx

Write-Host "Real-data pilot run finished"
Write-Host "Excel: outputs\excel\pilot_10.xlsx"
Write-Host "Visual QA: outputs\debug_visual"
