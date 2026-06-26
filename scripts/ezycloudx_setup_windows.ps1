param(
    [switch]$WithWeb
)

$ErrorActionPreference = "Stop"

Set-Location (Resolve-Path "$PSScriptRoot\..")

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip

if ($WithWeb) {
    .\.venv\Scripts\python.exe -m pip install -e ".[web]"
} else {
    .\.venv\Scripts\python.exe -m pip install -e .
}

New-Item -ItemType Directory -Force data\raw_pdfs\uploads | Out-Null
New-Item -ItemType Directory -Force outputs\excel | Out-Null
New-Item -ItemType Directory -Force outputs\json | Out-Null

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
}

Write-Host "Ezycloudx Windows setup done."
Write-Host "Default path does not require Ollama. Upload PDFs, then run .\scripts\ezycloudx_run_sample_windows.ps1."
