[CmdletBinding()]
param(
    [switch]$InstallDependencies,
    [switch]$SkipDatabase,
    [switch]$SkipMigration
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
$webRoot = Join-Path $repoRoot "apps\web"
$composePath = Join-Path $repoRoot "ops\web_demo\docker-compose.postgres.yml"
$backendScript = Join-Path $PSScriptRoot "run_backend.ps1"
$frontendScript = Join-Path $PSScriptRoot "run_frontend.ps1"
$runtimeRoot = Join-Path $env:LOCALAPPDATA "court-ocr-extract\web-demo"
$statePath = Join-Path $runtimeRoot "runtime-state.json"
$backendLog = Join-Path $runtimeRoot "backend.log"
$backendErrorLog = Join-Path $runtimeRoot "backend-error.log"
$frontendLog = Join-Path $runtimeRoot "frontend.log"
$frontendErrorLog = Join-Path $runtimeRoot "frontend-error.log"
$startedDatabase = $false
$backendLauncher = $null
$frontendLauncher = $null

function Test-LocalPort {
    param([int]$Port)
    $listeners = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().
        GetActiveTcpListeners()
    return $null -ne ($listeners | Where-Object { $_.Port -eq $Port } | Select-Object -First 1)
}

function Wait-LocalPort {
    param(
        [int]$Port,
        [int]$TimeoutSeconds = 30
    )
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (Test-LocalPort -Port $Port) {
            return
        }
        Start-Sleep -Milliseconds 500
    }
    throw "WEB-PORT-001: Port $Port did not become ready within $TimeoutSeconds seconds."
}

function Wait-Health {
    param(
        [string]$Uri,
        [string]$ErrorCode,
        [int]$TimeoutSeconds = 30
    )
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        try {
            $response = Invoke-RestMethod -Uri $Uri -TimeoutSec 3
            if ($response.status -eq "ok") {
                return $response
            }
        } catch {
            Start-Sleep -Milliseconds 500
        }
    }
    throw "${ErrorCode}: Health check did not pass at $Uri."
}

function Get-ListenerProcessId {
    param([int]$Port)
    $connection = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction Stop |
        Where-Object { $_.LocalAddress -in @("127.0.0.1", "::1") } |
        Select-Object -First 1
    if ($null -eq $connection) {
        throw "WEB-PORT-001: No loopback listener found on port $Port."
    }
    return [int]$connection.OwningProcess
}

function Wait-DatabaseReady {
    param([int]$TimeoutSeconds = 45)
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        docker compose -f $composePath exec postgres pg_isready -U web_demo_synthetic -d court_ocr_web_synthetic
        if ($LASTEXITCODE -eq 0) {
            return
        }
        Start-Sleep -Seconds 1
    }
    throw "WEB-DOCKER-STATE-001: PostgreSQL did not become ready within $TimeoutSeconds seconds."
}

function Stop-OwnedProcess {
    param([System.Diagnostics.Process]$Process)
    if ($null -eq $Process -or $Process.HasExited) {
        return
    }
    if (-not $Process.CloseMainWindow()) {
        Stop-Process -Id $Process.Id -ErrorAction SilentlyContinue
    }
}

Write-Output "Project Owner local launcher. Local loopback services only."

$branch = (git -C $repoRoot branch --show-current).Trim()
if ($branch -ne "demo-web-platform") {
    throw "WEB-PS-LAUNCHER-001: Expected branch demo-web-platform, found $branch."
}

$env:PYTHONPATH = Join-Path $repoRoot "src"
& (Join-Path $repoRoot ".venv\Scripts\python.exe") -c "import court_ocr_extract"
if ($LASTEXITCODE -ne 0) {
    throw "WEB-ALEMBIC-IMPORT-001: Python import failed. Use editable install or verify PYTHONPATH."
}

foreach ($port in @(3000, 8000)) {
    if (Test-LocalPort -Port $port) {
        throw "WEB-PORT-001: TCP port $port is already in use. Run status_local.ps1."
    }
}

New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null

try {
    & (Join-Path $PSScriptRoot "check_prerequisites.ps1")

    $dependenciesMissing = -not (Test-Path -LiteralPath (Join-Path $webRoot "node_modules") -PathType Container)
    if ($InstallDependencies -or $dependenciesMissing) {
        Push-Location -LiteralPath $webRoot
        try {
            npm.cmd ci
            npm.cmd audit
            npm.cmd audit --omit=dev
        } finally {
            Pop-Location
        }
    }

    if (-not $SkipDatabase) {
        docker compose -f $composePath up -d
        $startedDatabase = $true
        Wait-DatabaseReady
    }

    if (-not $SkipMigration) {
        $env:DATABASE_URL = "postgresql+psycopg://web_demo_synthetic:local_development_only@127.0.0.1:55432/court_ocr_web_synthetic"
        & (Join-Path $repoRoot ".venv\Scripts\python.exe") -m alembic upgrade head
        & (Join-Path $repoRoot ".venv\Scripts\python.exe") -m alembic current
    }

    $backendLauncher = Start-Process -FilePath "powershell.exe" -ArgumentList @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $backendScript
    ) -RedirectStandardOutput $backendLog -RedirectStandardError $backendErrorLog -PassThru -WindowStyle Hidden
    Wait-LocalPort -Port 8000
    $backendHealth = Wait-Health -Uri "http://127.0.0.1:8000/api/v1/system/health" -ErrorCode "WEB-PORT-001"
    $schema = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/system/schema" -TimeoutSec 5
    if (@($schema.columns).Count -ne 14) {
        throw "WEB-API-PROXY-001: Expected 14 schema columns."
    }

    $frontendLauncher = Start-Process -FilePath "powershell.exe" -ArgumentList @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $frontendScript
    ) -RedirectStandardOutput $frontendLog -RedirectStandardError $frontendErrorLog -PassThru -WindowStyle Hidden
    Wait-LocalPort -Port 3000
    $proxyHealth = Wait-Health -Uri "http://127.0.0.1:3000/api/v1/system/health" -ErrorCode "WEB-API-PROXY-001"

    $state = [ordered]@{
        repository = $repoRoot
        started_at_utc = [DateTime]::UtcNow.ToString("o")
        backend_pid = Get-ListenerProcessId -Port 8000
        frontend_pid = Get-ListenerProcessId -Port 3000
        backend_launcher_pid = $backendLauncher.Id
        frontend_launcher_pid = $frontendLauncher.Id
        database_started = $startedDatabase
    }
    $state | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding utf8
    Write-Output "Local web demo is ready: http://127.0.0.1:3000/dashboard"
    Write-Output "Backend health=$($backendHealth.status); proxy health=$($proxyHealth.status); schema columns=14"
    Write-Output "Runtime state: $statePath"
} catch {
    Stop-OwnedProcess -Process $frontendLauncher
    Stop-OwnedProcess -Process $backendLauncher
    if ($startedDatabase) {
        docker compose -f $composePath down
    }
    Remove-Item -LiteralPath $statePath -Force -ErrorAction SilentlyContinue
    throw
}
