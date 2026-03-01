# NOTE: Phase2 outbox sealing (append-only, robust)
# - Computes SHA256 + line counts for sync_*.jsonl into outbox.manifest.csv
# - Chains manifest rows into outbox.manifest.chain.csv
# - Verifies chain + file hashes
# NOTE: Handles 0/1/many files safely

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Sha256Hex([string]$s){
  $sha = [System.Security.Cryptography.SHA256]::Create()
  try{
    $b = [System.Text.Encoding]::UTF8.GetBytes($s)
    ($sha.ComputeHash($b) | ForEach-Object { $_.ToString("x2") }) -join ""
  } finally { $sha.Dispose() }
}

$root     = "C:\Users\sirok\MoCKA"
$outDir   = Join-Path $root "infield\ai_save\outbox"
$phase2   = Join-Path $root "infield\ai_save\phase2"
$manPath  = Join-Path $phase2 "outbox.manifest.csv"
$chainOut = Join-Path $phase2 "outbox.manifest.chain.csv"

if(-not (Test-Path $outDir)){ throw "outbox not found: $outDir" }
if(-not (Test-Path $phase2)){ New-Item -ItemType Directory -Force -Path $phase2 | Out-Null }

# --- 1) manifest ---
if(-not (Test-Path $manPath)){
  "ts,filename,sha256_hex,lines" | Set-Content -Path $manPath -Encoding UTF8
}

$known = @{}
$manLines = @(Get-Content $manPath -Encoding UTF8)
if($manLines.Count -gt 1){
  $manLines | Select-Object -Skip 1 | ForEach-Object {
    $p = $_.Split(",")
    if($p.Count -ge 2 -and $p[1]){ $known[$p[1]] = $true }
  }
}

$files = @(Get-ChildItem -Path $outDir -Filter "sync_*.jsonl" -File)
if($files.Count -eq 0){
  Write-Host "No sync_*.jsonl found in outbox."
}

foreach($f in $files | Sort-Object Name){
  if($known.ContainsKey($f.Name)){ continue }

  $hash  = (Get-FileHash -Algorithm SHA256 -Path $f.FullName).Hash.ToLower()
  $lines = @(Get-Content $f.FullName -Encoding UTF8).Count
  $ts    = (Get-Date).ToString("yyyy-MM-ddTHH:mm:sszzz")

  "$ts,$($f.Name),$hash,$lines" | Add-Content -Path $manPath -Encoding UTF8
}

# --- 2) chain ---
if(-not (Test-Path $chainOut)){
  "ts,filename,sha256_hex,lines,prev_chain_hash,chain_hash" | Set-Content -Path $chainOut -Encoding UTF8
}

$chained = @{}
$chainLines = @(Get-Content $chainOut -Encoding UTF8)
if($chainLines.Count -gt 1){
  $chainLines | Select-Object -Skip 1 | ForEach-Object {
    $p = $_.Split(",")
    if($p.Count -ge 2 -and $p[1]){ $chained[$p[1]] = $true }
  }
}

$prev = ""
if($chainLines.Count -gt 1){
  $lastRow = $chainLines[-1]
  if($lastRow -notmatch "^ts,"){
    $p = $lastRow.Split(",")
    if($p.Count -ge 6){ $prev = $p[5] }
  }
}

$manLines = @(Get-Content $manPath -Encoding UTF8)
if($manLines.Count -gt 1){
  $manLines | Select-Object -Skip 1 | ForEach-Object {
    $p = $_.Split(",")
    if($p.Count -lt 4){ return }
    $ts,$fn,$hx,$ln = $p[0],$p[1],$p[2],$p[3]
    if($chained.ContainsKey($fn)){ return }

    $material = "$ts|$fn|$hx|$ln|$prev"
    $ch = Sha256Hex $material

    "$ts,$fn,$hx,$ln,$prev,$ch" | Add-Content -Path $chainOut -Encoding UTF8
    $prev = $ch
  }
}

# --- 3) verify ---
$chainLines = @(Get-Content $chainOut -Encoding UTF8)
if($chainLines.Count -le 1){
  Write-Host "No chain entries to verify."
  exit 0
}

$rows = $chainLines | Select-Object -Skip 1
$prev = ""

foreach($r in $rows){
  $p = $r.Split(",")
  if($p.Count -lt 6){ throw "bad chain row: $r" }

  $ts,$fn,$hx,$ln,$prev_in,$ch = $p[0],$p[1],$p[2],$p[3],$p[4],$p[5]
  if($prev_in -ne $prev){ throw "BAD prev link: $fn" }

  $path = Join-Path $outDir $fn
  if(-not (Test-Path $path)){ throw "MISSING file: $fn" }

  $hash = (Get-FileHash -Algorithm SHA256 -Path $path).Hash.ToLower()
  if($hash -ne $hx){ throw "BAD hash: $fn" }

  $material = "$ts|$fn|$hx|$ln|$prev"
  $calc = Sha256Hex $material
  if($calc -ne $ch){ throw "BAD chain hash: $fn" }

  $prev = $ch
}

Write-Host "OK: outbox sealed and verified"
Write-Host ("LAST_CHAIN_HASH=" + $prev)
