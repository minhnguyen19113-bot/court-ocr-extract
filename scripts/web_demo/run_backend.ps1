[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
Set-Location -LiteralPath $repoRoot
$env:PYTHONPATH = Join-Path $repoRoot "src"

if ([string]::IsNullOrWhiteSpace($env:DATABASE_URL)) {
    $env:DATABASE_URL = "postgresql+psycopg://web_demo_synthetic:local_development_only@127.0.0.1:55432/court_ocr_web_synthetic"
}

.venv\Scripts\python.exe -m uvicorn court_ocr_extract.web_api.app:app --host 127.0.0.1 --port 8000
