param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$DockerExe = "C:\Program Files\Docker\Docker\resources\bin\docker.exe",
    [switch]$PersistUserEnvironment
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $DockerExe -PathType Leaf)) {
    throw "Docker executable not found: $DockerExe"
}

$toolsDir = Join-Path $ProjectRoot "tools"
$dockerShim = Join-Path $toolsDir "docker.cmd"
if ($dockerShim -match "\s") {
    throw "Docker shim path must not contain spaces. Use a project root such as C:\court-ocr-extract."
}

New-Item -ItemType Directory -Path $toolsDir -Force | Out-Null
$shimContent = "@echo off`r`n`"$DockerExe`" %*`r`n"
Set-Content -LiteralPath $dockerShim -Value $shimContent -Encoding Ascii -NoNewline

$runtimeEnvironment = [ordered]@{
    SURYA_INFERENCE_BACKEND = "vllm"
    SURYA_INFERENCE_KEEP_ALIVE = "1"
    SURYA_DOCKER_BINARY = $dockerShim
    DOCKER_BINARY = $dockerShim
    DOCKER_HOST = "npipe:////./pipe/docker_engine"
}

foreach ($entry in $runtimeEnvironment.GetEnumerator()) {
    Set-Item -Path "Env:$($entry.Key)" -Value $entry.Value
    if ($PersistUserEnvironment) {
        [Environment]::SetEnvironmentVariable($entry.Key, $entry.Value, "User")
    }
}

$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$persistNote = if ($PersistUserEnvironment) { "session hien tai va User environment" } else { "session PowerShell hien tai" }

Write-Host "Da tao Docker shim: $dockerShim"
Write-Host "Da set Surya/vLLM environment cho $persistNote."
Write-Host "Khong dung container surya-vllm-* sau khi runtime da warm."
Write-Host "Neu Windows Firewall/Docker hoi network access tren VM, allow ca Private va Public."
Write-Host ""
Write-Host "1. Kiem tra GPU container:"
Write-Host "& `"$python`" -B -m scripts.check_surya_runtime_backend --check-gpu-container --surya-docker-binary `"$dockerShim`""
Write-Host ""
Write-Host "2. OCR page 1 safe mode:"
Write-Host @"
& "$python" -m court_ocr_extract.cli debug-ocr-review ``
  --input data\raw_pdfs\pilot_one ``
  --limit 1 ``
  --review-sample-size 1 ``
  --ocr-backend surya ``
  --pages 1 ``
  --use-preprocessed ``
  --deskew off ``
  --red-seal-removal on ``
  --red-removal-mode inpaint ``
  --text-enhance medium ``
  --preprocess-profile balanced ``
  --stamp-suppression balanced ``
  --stamp-erase-mode mask ``
  --ocr-stamp-filter balanced ``
  --surya-docker-binary "$dockerShim" ``
  --surya-runtime-check-gpu-container ``
  --surya-startup-timeout-seconds 900 ``
  --output outputs\debug_visual_ocr_safe_mask_page1 ``
  --open
"@
