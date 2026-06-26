$ErrorActionPreference = "Stop"

Set-Location (Resolve-Path "$PSScriptRoot\..")

if ($env:LLAMA_CPP_BINARY -eq $null -or $env:LLAMA_CPP_BINARY -eq "") {
    $env:LLAMA_CPP_BINARY = [Environment]::GetEnvironmentVariable("LLAMA_CPP_BINARY", "User")
}
$env:SURYA_INFERENCE_BACKEND = if ($env:SURYA_INFERENCE_BACKEND) { $env:SURYA_INFERENCE_BACKEND } else { "llamacpp" }
$env:SURYA_INFERENCE_PARALLEL = if ($env:SURYA_INFERENCE_PARALLEL) { $env:SURYA_INFERENCE_PARALLEL } else { "1" }

.\.venv\Scripts\python.exe -m uvicorn app_fastapi.main:app --host 0.0.0.0 --port 8000
