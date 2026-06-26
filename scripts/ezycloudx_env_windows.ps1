function Resolve-LlamaCppBinary {
    if ($env:LLAMA_CPP_BINARY -and (Test-Path -LiteralPath $env:LLAMA_CPP_BINARY)) {
        return (Resolve-Path -LiteralPath $env:LLAMA_CPP_BINARY).Path
    }

    $userValue = [Environment]::GetEnvironmentVariable("LLAMA_CPP_BINARY", "User")
    if ($userValue -and (Test-Path -LiteralPath $userValue)) {
        return (Resolve-Path -LiteralPath $userValue).Path
    }

    $searchRoots = @("C:\tools\llama.cpp", "C:\tools")
    foreach ($root in $searchRoots) {
        if (-not (Test-Path -LiteralPath $root)) {
            continue
        }
        $candidate = Get-ChildItem -LiteralPath $root -Recurse -Filter "llama-server.exe" -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($candidate) {
            return $candidate.FullName
        }
    }

    return $null
}

function Initialize-EzycloudxRuntimeEnv {
    $llamaServer = Resolve-LlamaCppBinary
    if (-not $llamaServer) {
        throw @"
llama-server.exe was not found.

Install llama.cpp Windows build, then set LLAMA_CPP_BINARY. Quick check:
  Get-ChildItem C:\tools\llama.cpp -Recurse -Filter llama-server.exe

If it prints a path, set it:
  `$llamaServer = (Get-ChildItem C:\tools\llama.cpp -Recurse -Filter llama-server.exe | Select-Object -First 1).FullName
  [Environment]::SetEnvironmentVariable("LLAMA_CPP_BINARY", `$llamaServer, "User")
  `$env:LLAMA_CPP_BINARY = `$llamaServer
"@
    }

    $env:LLAMA_CPP_BINARY = $llamaServer
    [Environment]::SetEnvironmentVariable("LLAMA_CPP_BINARY", $llamaServer, "User")
    $env:SURYA_INFERENCE_BACKEND = if ($env:SURYA_INFERENCE_BACKEND) { $env:SURYA_INFERENCE_BACKEND } else { "llamacpp" }
    $env:SURYA_INFERENCE_PARALLEL = if ($env:SURYA_INFERENCE_PARALLEL) { $env:SURYA_INFERENCE_PARALLEL } else { "1" }

    Write-Host "Using LLAMA_CPP_BINARY=$env:LLAMA_CPP_BINARY"
}
