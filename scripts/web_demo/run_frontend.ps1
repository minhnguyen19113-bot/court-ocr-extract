[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
$webRoot = Join-Path $repoRoot "apps\web"
Set-Location -LiteralPath $webRoot

$env:WEB_API_ORIGIN = "http://127.0.0.1:8000"
$env:NEXT_PUBLIC_API_BASE_URL = "/api/v1"

npm.cmd run dev -- --hostname 127.0.0.1 --port 3000
