# NOTE: Phase2 diff extractor (append-only, robust)
# - Reads:  C:\Users\sirok\MoCKA\infield\ai_save\index.csv
# - Writes: C:\Users\sirok\MoCKA\infield\ai_save\outbox\sync_<run_id>.jsonl
# - Diff state: C:\Users\sirok\MoCKA\infield\ai_save\phase2\diff_state.json
# NOTE: Separate diff_state.json from seal checkpoint state to avoid collisions

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-Sha256Hex([byte[]]$bytes){
  $sha = [System.Security.Cryptography.SHA256]::Create()
  try { ($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString("x2") }) -join "" }
  finally { $sha.Dispose() }
}

$root      = "C:\Users\sirok\MoCKA"
$indexPath = Join-Path $root "infield\ai_save\index.csv"
$outDir    = Join-Path $root "infield\ai_save\outbox"
$statePath = Join-Path $root "infield\ai_save\phase2\diff_state.json"

if(-not (Test-Path $indexPath)){ throw "index.csv not found: $indexPath" }
if(-not (Test-Path $outDir)){ New-Item -ItemType Directory -Force -Path $outDir | Out-Null }

# --- Load diff state safely ---
$lastLineNo = 1
if(Test-Path $statePath){
  try{
    $raw = (Get-Content $statePath -Raw)
    if($raw -and $raw.Trim().Length -gt 0){
      $json = $raw | ConvertFrom-Json
      if($null -ne $json.last_line_no){
        $lastLineNo = [int]$json.last_line_no
      }
    }
  } catch {
    Write-Host "WARNING: diff_state.json unreadable. Reset last_line_no=1"
    $lastLineNo = 1
  }
}
if($lastLineNo -lt 1){ $lastLineNo = 1 }

$lines = @(Get-Content $indexPath -Encoding UTF8)
if($lines.Count -lt 1){ throw "index.csv is empty: $indexPath" }

$headers = $lines[0].Split(",") | ForEach-Object { $_.Trim() }

$startIdx = $lastLineNo
if($startIdx -ge $lines.Count){
  Write-Host "No new lines."
  exit 0
}

$runId   = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
$outPath = Join-Path $outDir ("sync_{0}.jsonl" -f $runId)

$seq = 0
for($i = $startIdx; $i -lt $lines.Count; $i++){
  $line = $lines[$i]
  if([string]::IsNullOrWhiteSpace($line)){ continue }

  $obj = $null
  try { $obj = $line | ConvertFrom-Csv -Header $headers }
  catch { $obj = [pscustomobject]@{ _raw = $line } }

  $rowHash = "sha256:" + (Get-Sha256Hex([System.Text.Encoding]::UTF8.GetBytes($line)))

  $packet = [ordered]@{
    packet_version = "0.1"
    run_id         = $runId
    seq            = $seq
    source         = [ordered]@{
      path    = "infield/ai_save/index.csv"
      line_no = ($i + 1)
    }
    row         = $obj
    row_hash    = $rowHash
    observed_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:sszzz")
  }

  ($packet | ConvertTo-Json -Depth 8 -Compress) | Add-Content -Path $outPath -Encoding UTF8
  $seq++
}

# --- Update diff state ---
$diffState = [ordered]@{
  last_line_no = $lines.Count
  last_line_no_recorded_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:sszzz")
}
($diffState | ConvertTo-Json -Depth 8) | Set-Content -Path $statePath -Encoding UTF8

Write-Host "OK: emitted=$seq out=$outPath diff_state_last_line_no=$($diffState["last_line_no"])"

