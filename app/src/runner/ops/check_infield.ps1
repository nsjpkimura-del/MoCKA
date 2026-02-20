param(
  [string]$RepoRoot = "."
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail([string]$msg) { Write-Host $msg; exit 1 }
function Pass([string]$msg) { Write-Host $msg }

function Find-Up([string]$start, [string]$relativePath) {
  $dir = (Resolve-Path $start).Path
  while ($true) {
    $candidate = Join-Path $dir $relativePath
    if (Test-Path $candidate) { return $candidate }
    $parent = Split-Path -Parent $dir
    if ($parent -eq $dir -or [string]::IsNullOrEmpty($parent)) { break }
    $dir = $parent
  }
  return $null
}

$root = (Resolve-Path $RepoRoot).Path

# 1) SSOT file existence (search upward from RepoRoot)
$ssotPath = Find-Up $root "docs\SSOT.md"
if (-not $ssotPath) { Fail "SSOT missing: docs/SSOT.md (searched upward)" }
Pass ("OK: SSOT exists: " + $ssotPath)

# 2) .env canon existence (search upward from RepoRoot)
$envCanon = Find-Up $root "mocka_orchestrator\.env"
if (-not $envCanon) { Fail "Config canon missing: mocka_orchestrator/.env (searched upward)" }
Pass ("OK: env canon found: " + $envCanon)

# 3) Ensure there are no other .env files under the PROJECT ROOT (the directory containing env canon)
$projectRoot = Split-Path -Parent (Split-Path -Parent $envCanon)  # parent of mocka_orchestrator
$allowedEnv = $envCanon

$envFiles = Get-ChildItem -Path $projectRoot -Recurse -Force -File -Filter ".env" -ErrorAction SilentlyContinue
$envBad = @()
foreach ($f in $envFiles) {
  if ($f.FullName -ne $allowedEnv) { $envBad += $f.FullName }
}

if ($envBad.Count -gt 0) {
  Write-Host "Prohibited .env files found:"
  $envBad | ForEach-Object { Write-Host $_ }
  Fail "Violation: extra .env files"
}
Pass "OK: .env canon enforced (project root scope)"

# 4) Canonical entrypoint existence (must be in RepoRoot)
$entry = Join-Path $root "run_infield_retry_worker.cmd"
if (-not (Test-Path $entry)) { Fail "Entrypoint missing in RepoRoot: run_infield_retry_worker.cmd" }
Pass "OK: entrypoint exists"

# 5) Detect old runner references (search in project root)
$patterns = @(
  "mocka-infield",
  "runner_out",
  "runner_error"
)

$hits = @()
foreach ($p in $patterns) {
  $r = Select-String -Path (Join-Path $projectRoot "*") -Pattern $p -Recurse -Force -ErrorAction SilentlyContinue
  if ($r) { $hits += $r }
}

if ($hits.Count -gt 0) {
  Write-Host "Prohibited references found:"
  $hits | ForEach-Object { Write-Host ("{0}:{1}:{2}" -f $_.Path, $_.LineNumber, $_.Line.Trim()) }
  Fail "Violation: old runner references"
}
Pass "OK: no old runner references detected"

Pass "DONE: structural gate passed"
exit 0
