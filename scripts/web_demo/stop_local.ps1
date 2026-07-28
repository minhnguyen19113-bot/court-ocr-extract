[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
$composePath = Join-Path $repoRoot "ops\web_demo\docker-compose.postgres.yml"
$runtimeRoot = Join-Path $env:LOCALAPPDATA "court-ocr-extract\web-demo"
$statePath = Join-Path $runtimeRoot "runtime-state.json"
$nextPath = Join-Path $repoRoot "apps\web\.next"

function Stop-ExactProcess {
    param(
        [int]$ProcessId,
        [string]$Name
    )
    if ($ProcessId -le 0) {
        return
    }
    $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($null -eq $process) {
        Write-Output "[STOPPED] $Name PID=$ProcessId was not running."
        return
    }
    if ($process.CloseMainWindow()) {
        if (-not $process.WaitForExit(5000)) {
            taskkill.exe /PID $ProcessId | Out-Null
        }
    } else {
        taskkill.exe /PID $ProcessId | Out-Null
    }
    Write-Output "[STOPPED] $Name PID=$ProcessId"
}

if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) {
    Write-Output "[NO STATE] Nothing will be stopped without an exact runtime-state PID."
    exit 0
}

$state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
Stop-ExactProcess -ProcessId ([int]$state.frontend_pid) -Name "frontend"
Stop-ExactProcess -ProcessId ([int]$state.backend_pid) -Name "backend"
Stop-ExactProcess -ProcessId ([int]$state.frontend_launcher_pid) -Name "frontend launcher"
Stop-ExactProcess -ProcessId ([int]$state.backend_launcher_pid) -Name "backend launcher"

if ([bool]$state.database_started) {
    docker compose -f $composePath down
}

$frontendPort = Get-NetTCPConnection -State Listen -LocalPort 3000 -ErrorAction SilentlyContinue
$repoFrontend = Get-CimInstance Win32_Process |
    Where-Object {
        $_.CommandLine -like "*$repoRoot\apps\web*" -and
        $_.Name -in @("node.exe", "powershell.exe", "pwsh.exe")
    } |
    Select-Object -First 1
if (
    $null -eq $frontendPort -and
    $null -eq $repoFrontend -and
    (Test-Path -LiteralPath $nextPath -PathType Container)
) {
    Remove-Item -LiteralPath $nextPath -Recurse -Force
}

Remove-Item -LiteralPath $statePath -Force
foreach ($logName in @("backend.log", "backend-error.log", "frontend.log", "frontend-error.log")) {
    Remove-Item -LiteralPath (Join-Path $runtimeRoot $logName) -Force -ErrorAction SilentlyContinue
}

foreach ($port in @(3000, 8000, 55432)) {
    $listener = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
    if ($null -eq $listener) {
        Write-Output "[FREE] port=$port"
    } else {
        Write-Output "[IN USE] port=$port; no additional process was stopped."
    }
}
Write-Output "Web demo local runtime stopped."
