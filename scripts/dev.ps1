[CmdletBinding()]
param(
    [switch]$Stop
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$FrontendRoot = Join-Path $ProjectRoot "frontend"
$RuntimeRoot = Join-Path $ProjectRoot "data\dev-runtime"
$LogRoot = Join-Path $RuntimeRoot "logs"
$StateFile = Join-Path $RuntimeRoot "processes.json"

function Test-HttpEndpoint {
    param([Parameter(Mandatory)][string]$Uri)

    try {
        $null = Invoke-WebRequest -Uri $Uri -UseBasicParsing -TimeoutSec 2
        return $true
    }
    catch {
        return $false
    }
}

function Wait-ForEndpoint {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$Uri,
        [int]$TimeoutSeconds = 30
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-HttpEndpoint -Uri $Uri) {
            Write-Host "[ready] $Name - $Uri" -ForegroundColor Green
            return
        }
        Start-Sleep -Milliseconds 500
    }
    throw "$Name did not become ready within $TimeoutSeconds seconds. Check $LogRoot."
}

function Save-ProcessState {
    param([Parameter(Mandatory)][array]$Processes)

    New-Item -ItemType Directory -Force -Path $RuntimeRoot | Out-Null
    ConvertTo-Json -InputObject $Processes -Depth 4 | Set-Content -LiteralPath $StateFile -Encoding utf8
}

function Start-DevProcess {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][string[]]$ArgumentList,
        [Parameter(Mandatory)][string]$WorkingDirectory
    )

    New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null
    $stdoutPath = Join-Path $LogRoot "$Name.out.log"
    $stderrPath = Join-Path $LogRoot "$Name.err.log"
    $process = Start-Process `
        -FilePath $FilePath `
        -ArgumentList $ArgumentList `
        -WorkingDirectory $WorkingDirectory `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdoutPath `
        -RedirectStandardError $stderrPath `
        -PassThru

    Write-Host "[start] $Name (PID $($process.Id))" -ForegroundColor Cyan
    return [pscustomobject]@{
        name = $Name
        pid = $process.Id
        start_time = $process.StartTime.ToUniversalTime().ToString("o")
    }
}

function Stop-OwnedProcessTree {
    param([Parameter(Mandatory)]$Entry)

    $process = Get-Process -Id $Entry.pid -ErrorAction SilentlyContinue
    if (-not $process) {
        Write-Host "[stopped] $($Entry.name) was not running."
        return
    }

    $recordedStart = [datetime]::Parse($Entry.start_time).ToUniversalTime()
    $actualStart = $process.StartTime.ToUniversalTime()
    if ([math]::Abs(($actualStart - $recordedStart).TotalSeconds) -gt 2) {
        Write-Warning "Skipped PID $($Entry.pid): it has been reused by another process."
        return
    }

    $descendants = Get-CimInstance Win32_Process | Where-Object {
        $_.ParentProcessId -eq $Entry.pid
    }
    foreach ($child in $descendants) {
        Stop-OwnedProcessTree -Entry ([pscustomobject]@{
            name = "$($Entry.name) child"
            pid = $child.ProcessId
            start_time = (Get-Process -Id $child.ProcessId).StartTime.ToUniversalTime().ToString("o")
        })
    }
    Stop-Process -Id $Entry.pid -Force -ErrorAction SilentlyContinue
    Write-Host "[stopped] $($Entry.name) (PID $($Entry.pid))" -ForegroundColor Yellow
}

if ($Stop) {
    if (-not (Test-Path -LiteralPath $StateFile)) {
        Write-Host "No CyberSRS processes were started by this launcher."
        exit 0
    }
    $ownedProcesses = @(Get-Content -LiteralPath $StateFile -Raw | ConvertFrom-Json)
    [array]::Reverse($ownedProcesses)
    foreach ($entry in $ownedProcesses) {
        Stop-OwnedProcessTree -Entry $entry
    }
    Remove-Item -LiteralPath $StateFile -Force
    exit 0
}

$trackedProcesses = @()
if (Test-Path -LiteralPath $StateFile) {
    $trackedProcesses = @(Get-Content -LiteralPath $StateFile -Raw | ConvertFrom-Json)
}

$ollamaUri = "http://127.0.0.1:11434/api/tags"
if (Test-HttpEndpoint -Uri $ollamaUri) {
    Write-Host "[ready] Ollama is already running." -ForegroundColor Green
}
else {
    $ollamaCommand = (Get-Command ollama -ErrorAction Stop).Source
    $trackedProcesses += Start-DevProcess -Name "ollama" -FilePath $ollamaCommand -ArgumentList @("serve") -WorkingDirectory $ProjectRoot
    Save-ProcessState -Processes $trackedProcesses
    Wait-ForEndpoint -Name "Ollama" -Uri $ollamaUri
}

$backendUri = "http://127.0.0.1:8000/api/v1/health"
if (Test-HttpEndpoint -Uri $backendUri) {
    Write-Host "[ready] Backend is already running." -ForegroundColor Green
}
else {
    $pythonCommand = (Get-Command python -ErrorAction Stop).Source
    $trackedProcesses += Start-DevProcess `
        -Name "backend" `
        -FilePath $pythonCommand `
        -ArgumentList @("-m", "uvicorn", "src.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000") `
        -WorkingDirectory $ProjectRoot
    Save-ProcessState -Processes $trackedProcesses
    Wait-ForEndpoint -Name "Backend" -Uri $backendUri
}

$frontendUri = "http://127.0.0.1:5173"
if (Test-HttpEndpoint -Uri $frontendUri) {
    Write-Host "[ready] Frontend is already running." -ForegroundColor Green
}
else {
    $npmCommand = (Get-Command npm.cmd -ErrorAction Stop).Source
    $trackedProcesses += Start-DevProcess `
        -Name "frontend" `
        -FilePath $npmCommand `
        -ArgumentList @("run", "dev", "--", "--host", "127.0.0.1", "--strictPort") `
        -WorkingDirectory $FrontendRoot
    Save-ProcessState -Processes $trackedProcesses
    Wait-ForEndpoint -Name "Frontend" -Uri $frontendUri
}

Write-Host ""
Write-Host "CyberSRS is ready: $frontendUri" -ForegroundColor Green
Write-Host "Logs: $LogRoot"
Write-Host "Stop services started by this launcher: .\dev.cmd -Stop"
