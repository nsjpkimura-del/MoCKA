# NOTE: Phase2 one-shot runner (strict + beautiful)
# - If diff emits 0 new packets, skip sealing
# - Otherwise seal + checkpoint
# - Uses regex (NOT SimpleMatch) for correct detection

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = "C:\Users\sirok\MoCKA"
$diff = Join-Path $root "infield\ai_save\phase2\diff_extract.ps1"
$seal = Join-Path $root "infield\ai_save\phase2\seal_outbox.ps1"
$statePath = Join-Path $root "infield\ai_save\phase2\state.json"

# --- run diff ---
$out1 = powershell -ExecutionPolicy Bypass -File $diff
$out1 | ForEach-Object { $_ }

# --- detect no-op (regex) ---
$noNew = ($out1 | Select-String -Pattern "^No new lines\." | Select-Object -First 1)

if($noNew){
  Write-Host "OK: no new packets; skip seal"
  exit 0
}

# --- run seal ---
$out2 = powershell -ExecutionPolicy Bypass -File $seal
$out2 | ForEach-Object { $_ }

$last = ($out2 | Select-String -Pattern "^LAST_CHAIN_HASH=" | Select-Object -Last 1).Line
if(-not $last){ throw "LAST_CHAIN_HASH not found in seal_outbox output" }

$chain = $last.Split("=")[1].Trim()

# --- checkpoint ---
$state = @{}
if(Test-Path $statePath){
  try {
    $raw = Get-Content $statePath -Raw
    if($raw -and $raw.Trim().Length -gt 0){
      $j = $raw | ConvertFrom-Json
      foreach($p in $j.PSObject.Properties){
        $state[$p.Name] = $p.Value
      }
    }
  } catch { $state = @{} }
}

$state["last_chain_hash"] = $chain
$state["last_chain_hash_recorded_at"] = (Get-Date).ToString("yyyy-MM-ddTHH:mm:sszzz")

($state | ConvertTo-Json -Depth 8) | Set-Content -Path $statePath -Encoding UTF8

Write-Host "OK: phase2 one-shot complete"
Write-Host ("CHECKPOINT_CHAIN_HASH=" + $chain)
