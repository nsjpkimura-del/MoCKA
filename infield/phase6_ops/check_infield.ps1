param(
  [string]$RepoRoot = "."
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail([string]$msg) { Write-Host $msg; exit 1 }
function Pass([string]$msg) { Write-Host $msg }

$root = (Resolve-Path $RepoRoot).Path

# 1) SSOT file existence
$ssot = Join-Path $root "docs\SSOT.md"
if (-not (Test-Path $ssot)) { Fail "SSOT missing: docs/SSOT.md" }
Pass "OK: SSOT exists"

# 2) .env uniqueness (only mocka_orchestrator/.env allowed)
$allowedEnv = Join-Path $root "mocka_orchestrator\.env"
$envFiles = Get-ChildItem -Path $root -Recurse -Force -File -Filter ".env" -ErrorAction SilentlyContinue

$envBad = @()
foreach ($f in $envFiles) {
  if ($f.FullName -ne $allowedEnv) { $envBad += $f.FullName }
}

if (-not (Test-Path $allowedEnv)) { Fail "Config canon missing: mocka_orchestrator/.env" }
if ($envBad.Count -gt 0) {
  Write-Host "Prohibited .env files found:"
  $envBad | ForEach-Object { Write-Host $_ }
  Fail "Violation: extra .env files"
}
Pass "OK: .env canon enforced"

# 3) Canonical entrypoint existence
$entry = Join-Path $root "run_infield_retry_worker.cmd"
if (-not (Test-Path $entry)) { Fail "Entrypoint missing: run_infield_retry_worker.cmd" }
Pass "OK: entrypoint exists"

# 4) Detect old runner references (adjust patterns for your repo)
$patterns = @(
  "mocka-infield",
  "runner_out",
  "runner_error"
)

$hits = @()
foreach ($p in $patterns) {
  $r = Select-String -Path (Join-Path $root "*") -Pattern $p -Recurse -Force -ErrorAction SilentlyContinue
  if ($r) { $hits += $r }
}

if ($hits.Count -gt 0) {
  Write-Host "Prohibited references found:"
  $hits | ForEach-Object { Write-Host ("{0}:{1}:{2}" -f $_.Path, $_.LineNumber, $_.Line.Trim()) }
  Fail "Violation: old runner references"
}
Pass "OK: no old runner references detected"

# 5) Placeholder for regression checks
# Integrate your existing tests here:
# - concurrent dual start test
# - deadletter test

Pass "DONE: structural gate passed"
exit 0