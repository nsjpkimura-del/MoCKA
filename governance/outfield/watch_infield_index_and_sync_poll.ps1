# C:\Users\sirok\MoCKA\governance\outfield\watch_infield_index_and_sync_poll.ps1
# Polling watcher with single-instance lock
# Target Spreadsheet:
# https://docs.google.com/spreadsheets/d/1qwTXWG95pYyOOHCcL57UFI0bu33UZKErtSDQSwMawew/edit#gid=0

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$watchPath = "C:\Users\sirok\MoCKA\governance\infield\index"
$runner    = "C:\Users\sirok\MoCKA\governance\outfield\run_outfield_export_A.ps1"
$stateDir  = "C:\Users\sirok\MoCKA\governance\outfield\state"
$logPath   = Join-Path $stateDir "watcher_poll.log"
$stateHash = Join-Path $stateDir "index_dir.last_sha256.txt"
$lockFile  = Join-Path $stateDir "watcher_poll.lock"

if (!(Test-Path $watchPath)) { throw "watchPath not found: $watchPath" }
if (!(Test-Path $runner)) { throw "runner not found: $runner" }

New-Item -ItemType Directory -Force -Path $stateDir | Out-Null

# single instance lock
if (Test-Path $lockFile) {
  try {
    $pidText = (Get-Content $lockFile -Raw).Trim()
    if ($pidText) {
      $pid = [int]$pidText
      $p = Get-Process -Id $pid -ErrorAction SilentlyContinue
      if ($p) { exit 0 }
    }
  } catch { }
}
Set-Content -Encoding UTF8 -Path $lockFile -Value ($PID.ToString() + "
")

function Write-Log([string]$msg) {
  $ts = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffK")
  Add-Content -Encoding UTF8 -Path $logPath -Value "$ts 	$msg"
  Write-Host "$ts 	$msg"
}

function Get-DirSignature {
  param([string]$dir)
  $files = Get-ChildItem -Path $dir -Filter "*.csv" -File | Sort-Object FullName
  $sb = New-Object System.Text.StringBuilder
  foreach($f in $files){
    $line = "$($f.FullName)|$($f.Length)|$($f.LastWriteTimeUtc.ToString('o'))"
    [void]$sb.AppendLine($line)
  }
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($sb.ToString())
  $sha = [System.Security.Cryptography.SHA256]::Create()
  ($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString("x2") }) -join ""
}

Write-Log ("WATCHING(POLL): " + $watchPath)
Write-Log ("RUNNER:         " + $runner)
Write-Log ("LOG:            " + $logPath)
Write-Log ("LOCK:           " + $lockFile)
Write-Log "Press Ctrl+C to stop."

$last = ""
if (Test-Path $stateHash) { $last = (Get-Content $stateHash -Raw).Trim() }

try {
  while($true){
    try{
      $sig = Get-DirSignature -dir $watchPath
      if ($sig -ne $last){
        Write-Log ("CHANGE_DETECTED: " + $sig)

        $out = powershell -NoProfile -ExecutionPolicy Bypass -File $runner 2>&1 | Out-String
        Write-Log "RUNNER_OUTPUT_BEGIN"
        foreach ($line in ($out -split "?
")) {
          if ($line.Trim().Length -gt 0) { Write-Log $line }
        }
        Write-Log "RUNNER_OUTPUT_END"

        $last = $sig
        Set-Content -Encoding UTF8 -Path $stateHash -Value ($sig + "
")
      }
    } catch {
      Write-Log ("POLL_ERROR: " + $_.Exception.Message)
    }
    Start-Sleep -Seconds 2
  }
} finally {
  try { Remove-Item -Force $lockFile -ErrorAction SilentlyContinue } catch { }
}
