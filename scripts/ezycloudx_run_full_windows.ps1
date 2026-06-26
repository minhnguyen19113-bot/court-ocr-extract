param(
    [string]$InputDir = "data\raw_pdfs\uploads",
    [string]$Output = "outputs\excel\full_results.xlsx",
    [int]$MaxPagesBeforeMarker = 5,
    [int]$Dpi = 300,
    [switch]$UseLocalLlm,
    [switch]$NoForce
)

$ErrorActionPreference = "Stop"

Set-Location (Resolve-Path "$PSScriptRoot\..")

. "$PSScriptRoot\ezycloudx_env_windows.ps1"
Initialize-EzycloudxRuntimeEnv

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
