param(
    [string]$InputDir = "data\raw_pdfs\uploads",
    [string]$Output = "outputs\excel\result.xlsx",
    [int]$MaxPagesBeforeMarker = 5,
    [int]$Dpi = 300,
    [switch]$UseLocalLlm,
    [switch]$NoForce
)

$ErrorActionPreference = "Stop"

Set-Location (Resolve-Path "$PSScriptRoot\..")

if ($env:LLAMA_CPP_BINARY -eq $null -or $env:LLAMA_CPP_BINARY -eq "") {
    $env:LLAMA_CPP_BINARY = [Environment]::GetEnvironmentVariable("LLAMA_CPP_BINARY", "User")
}
$env:SURYA_INFERENCE_BACKEND = if ($env:SURYA_INFERENCE_BACKEND) { $env:SURYA_INFERENCE_BACKEND } else { "llamacpp" }
$env:SURYA_INFERENCE_PARALLEL = if ($env:SURYA_INFERENCE_PARALLEL) { $env:SURYA_INFERENCE_PARALLEL } else { "1" }

$ArgsList = @(
    "-m", "scripts.run_batch",
    "--input-dir", $InputDir,
    "--output", $Output,
    "--max-pages-before-marker", "$MaxPagesBeforeMarker",
    "--dpi", "$Dpi",
    "--stop-on-marker",
    "--remove-red-stamp"
)

if ($UseLocalLlm) {
    $ArgsList += "--use-local-llm"
} else {
    $ArgsList += "--no-local-llm"
}

if (-not $NoForce) {
    $ArgsList += "--force"
}

.\.venv\Scripts\python.exe @ArgsList
