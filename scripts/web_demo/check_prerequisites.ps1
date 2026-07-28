[CmdletBinding()]
param(
    [int[]]$Ports = @(3000, 8000, 55432)
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
$webRoot = Join-Path $repoRoot "apps\web"
$lockPath = Join-Path $webRoot "package-lock.json"
$environmentExample = Join-Path $repoRoot ".env.web.example"
$pythonPath = Join-Path $repoRoot ".venv\Scripts\python.exe"
$composePath = Join-Path $repoRoot "ops\web_demo\docker-compose.postgres.yml"
$backendScript = Join-Path $PSScriptRoot "run_backend.ps1"
$frontendScript = Join-Path $PSScriptRoot "run_frontend.ps1"

Write-Output "Web demo prerequisite check (read-only)"
Write-Output "Repository: $repoRoot"

$branch = (git -C $repoRoot branch --show-current).Trim()
if ($branch -eq "demo-web-platform") {
    Write-Output "[OK] Branch -> $branch"
} else {
    Write-Output "[MISMATCH] Branch -> $branch (expected demo-web-platform)"
}

$nodeCommand = Get-Command "node" -ErrorAction SilentlyContinue
$npmCommand = Get-Command "npm.cmd" -ErrorAction SilentlyContinue
$systemNodeRoot = Join-Path $env:ProgramFiles "nodejs"
$nodeFallback = Join-Path $systemNodeRoot "node.exe"
$npmFallback = Join-Path $systemNodeRoot "npm.cmd"
$nodePath = if ($null -ne $nodeCommand) {
    $nodeCommand.Source
} elseif (Test-Path -LiteralPath $nodeFallback -PathType Leaf) {
    $nodeFallback
}
$npmPath = if ($null -ne $npmCommand) {
    $npmCommand.Source
} elseif (Test-Path -LiteralPath $npmFallback -PathType Leaf) {
    $npmFallback
}
$nodeReady = -not [string]::IsNullOrWhiteSpace($nodePath)
$npmReady = -not [string]::IsNullOrWhiteSpace($npmPath)

if ($nodeReady) {
    $nodeVersion = (& $nodePath --version).Trim()
    Write-Output "[OK] node -> $nodePath ($nodeVersion)"
} else {
    Write-Output "[MISSING] node"
}

if ($npmReady) {
    $npmVersion = (& $npmPath --version).Trim()
    Write-Output "[OK] npm -> $npmPath ($npmVersion)"
} else {
    Write-Output "[MISSING] npm"
}

if (Test-Path -LiteralPath $pythonPath -PathType Leaf) {
    Write-Output "[OK] Python venv -> $pythonPath"
    $importResult = & $pythonPath -c "import court_ocr_extract; print('ok')" 2>$null
    if ($LASTEXITCODE -eq 0 -and $importResult -contains "ok") {
        Write-Output "[OK] Python import -> court_ocr_extract"
    } else {
        Write-Output "[MISSING] Python import -> court_ocr_extract"
        Write-Output "[GUIDANCE] Use editable install or set PYTHONPATH to <REPO_ROOT>\src."
    }
} else {
    Write-Output "[MISSING] Python venv -> $pythonPath"
}

if (Test-Path -LiteralPath $lockPath -PathType Leaf) {
    Write-Output "[OK] package-lock.json"
} else {
    Write-Output "[MISSING] package-lock.json"
}

if (Test-Path -LiteralPath $environmentExample -PathType Leaf) {
    Write-Output "[OK] .env.web.example"
} else {
    Write-Output "[MISSING] .env.web.example"
}

$dockerCommand = Get-Command "docker" -ErrorAction SilentlyContinue
if ($null -ne $dockerCommand) {
    Write-Output "[OK] Container CLI -> $($dockerCommand.Source)"
    $daemonState = docker info --format "{{.ServerVersion}}" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Output "[OK] Container daemon -> $daemonState"
    } else {
        Write-Output "[MISSING] Container daemon"
    }
} else {
    Write-Output "[MISSING] Container CLI"
}

foreach ($requiredPath in @($composePath, $backendScript, $frontendScript)) {
    if (Test-Path -LiteralPath $requiredPath -PathType Leaf) {
        Write-Output "[OK] Required file -> $requiredPath"
    } else {
        Write-Output "[MISSING] Required file -> $requiredPath"
    }
}

$activePorts = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().
    GetActiveTcpListeners() |
    Select-Object -ExpandProperty Port -Unique

foreach ($port in $Ports) {
    if ($activePorts -contains $port) {
        Write-Output "[IN USE] TCP port $port"
    } else {
        Write-Output "[FREE] TCP port $port"
    }
}

Write-Output "Script does not install dependencies, start services, open ports, or change the machine."
Write-Output "See docs/web_demo/OPERATIONS_RUNBOOK.md for Project Owner commands."

if (
    -not $nodeReady -or
    -not $npmReady -or
    $branch -ne "demo-web-platform" -or
    -not (Test-Path -LiteralPath $pythonPath -PathType Leaf) -or
    -not (Test-Path -LiteralPath $lockPath -PathType Leaf) -or
    -not (Test-Path -LiteralPath $composePath -PathType Leaf)
) {
    exit 1
}

exit 0
