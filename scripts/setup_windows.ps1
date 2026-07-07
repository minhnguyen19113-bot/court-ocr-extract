param(
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

Write-Host "Checking Python..."
& $Python --version

if (-not (Test-Path ".venv")) {
  & $Python -m venv .venv
}

.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .

if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
}

Write-Host "Setup done. Edit .env before running OCR/extraction."
