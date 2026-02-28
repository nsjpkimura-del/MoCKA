# C:\Users\sirok\MoCKA\governance\outfield\watch_infield_index_and_sync.ps1
# Watch infield index changes -> run one-shot sync (debounced) with logging
# Target Spreadsheet:
# https://docs.google.com/spreadsheets/d/1qwTXWG95pYyOOHCcL57UFI0bu33UZKErtSDQSwMawew/edit#gid=0

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$watchPath = "C:\Users\sirok\MoCKA\governance\infield\index"
$runner    = "C:\Users\sirok\MoCKA\governance\outfield\run_outfield_export_A.ps1"
$logDir    = "C:\Users\sirok\MoCKA\governance\outfield\state"
$logPath   = Join-Path $logDir "watcher.log"

if (!(Test-Path $watchPath)) { throw "watchPath not found: $watchPath" }
if (!(Test-Path $runner)) { throw "runner not found: $runner" }

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Write-Log([string]$msg) {
  $ts = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffK")
  $line = "$ts 	$msg"
  Add-Content -Encoding UTF8 -Path $logPath -Value $line
  Write-Host $line
}

$fsw = New-Object System.IO.FileSystemWatcher
$fsw.Path = $watchPath
$fsw.Filter = "*.csv"
$fsw.IncludeSubdirectories = $false
$fsw.NotifyFilter = [System.IO.NotifyFilters]'FileName, LastWrite, Size'
$fsw.EnableRaisingEvents = $true

$script:LastRun = Get-Date "2000-01-01"
$script:MinIntervalSeconds = 2

$action = {
  try {
    $now = Get-Date
    if (($now - $script:LastRun).TotalSeconds -lt $script:MinIntervalSeconds) {
      return
    }
    $script:LastRun = $now

    Write-Log ("EVENT: " + $Event.SourceEventArgs.ChangeType + " " + $Event.SourceEventArgs.FullPath)

    $out = powershell -NoProfile -ExecutionPolicy Bypass -File $using:runner 2>&1 | Out-String
    Write-Log "RUNNER_OUTPUT_BEGIN"
    foreach ($line in ($out -split "?
")) {
      if ($line.Trim().Length -gt 0) { Write-Log $line }
    }
    Write-Log "RUNNER_OUTPUT_END"
  } catch {
    Write-Log ("WATCH_ERROR: " + $_.Exception.Message)
  }
}

Register-ObjectEvent -InputObject $fsw -EventName Changed -Action $action | Out-Null
Register-ObjectEvent -InputObject $fsw -EventName Created -Action $action | Out-Null
Register-ObjectEvent -InputObject $fsw -EventName Renamed -Action $action | Out-Null

Write-Log ("WATCHING: " + $watchPath)
Write-Log ("RUNNER:   " + $runner)
Write-Log ("LOG:      " + $logPath)
Write-Log "Press Ctrl+C to stop."

while ($true) { Start-Sleep -Seconds 3600 }
