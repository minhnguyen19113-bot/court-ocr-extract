[CmdletBinding()]
param()

$ErrorActionPreference = "Continue"
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
$composePath = Join-Path $repoRoot "ops\web_demo\docker-compose.postgres.yml"
$runtimeRoot = Join-Path $env:LOCALAPPDATA "court-ocr-extract\web-demo"
$statePath = Join-Path $runtimeRoot "runtime-state.json"
$nextPath = Join-Path $repoRoot "apps\web\.next"
$state = $null

Write-Output "Web demo local status (read-only)"
$branch = (git -C $repoRoot branch --show-current).Trim()
Write-Output "[GIT] branch=$branch"
$statusLines = @(git -C $repoRoot status --short)
Write-Output "[GIT] changed_paths=$($statusLines.Count)"

if (Test-Path -LiteralPath $statePath -PathType Leaf) {
    $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    Write-Output "[STATE] $statePath"
} else {
    Write-Output "[NO STATE] $statePath"
}

$daemonVersion = docker info --format "{{.ServerVersion}}" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Output "[DOCKER] daemon ready: $daemonVersion"
    docker compose -f $composePath ps
} else {
    Write-Output "[DOCKER] daemon unavailable"
}

foreach ($port in @(3000, 8000, 55432)) {
    $listeners = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
    if ($null -eq $listeners) {
        Write-Output "[FREE] port=$port"
        continue
    }
    foreach ($listener in $listeners) {
        $process = Get-Process -Id $listener.OwningProcess -ErrorAction SilentlyContinue
        $command = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)" |
            Select-Object -ExpandProperty CommandLine
        $owner = if ($command -like "*$repoRoot*") { "repository" } else { "external-or-unknown" }
        Write-Output "[LISTEN] port=$port PID=$($listener.OwningProcess) process=$($process.ProcessName) owner=$owner"
        if ($owner -eq "repository") {
            $safeCommand = $command.Replace($repoRoot, "<REPO_ROOT>")
            Write-Output "[COMMAND] $safeCommand"
        }
    }
}

foreach ($health in @(
    @{ Name = "backend"; Uri = "http://127.0.0.1:8000/api/v1/system/health" },
    @{ Name = "frontend-proxy"; Uri = "http://127.0.0.1:3000/api/v1/system/health" }
)) {
    try {
        $response = Invoke-RestMethod -Uri $health.Uri -TimeoutSec 3
        Write-Output "[HEALTH] $($health.Name) status=$($response.status)"
    } catch {
        Write-Output "[HEALTH] $($health.Name) unavailable"
    }
}

try {
    $schema = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/system/schema" -TimeoutSec 3
    $columnCount = @($schema.columns).Count
    Write-Output "[SCHEMA] column_count=$columnCount"
} catch {
    Write-Output "[SCHEMA] unavailable"
}

if (Test-Path -LiteralPath $nextPath -PathType Container) {
    Write-Output "[NEXT CACHE] present: <REPO_ROOT>\apps\web\.next"
} else {
    Write-Output "[NEXT CACHE] absent"
}
