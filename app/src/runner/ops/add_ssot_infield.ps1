param(
  [string]$RepoRoot = ".",
  [string]$EntrypointCmd = "run_infield_retry_worker.cmd"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Info([string]$msg) { Write-Host $msg }
function Fail([string]$msg) { throw $msg }

function Ensure-Dir([string]$path) {
  if (-not (Test-Path $path)) { New-Item -ItemType Directory -Path $path -Force | Out-Null }
}

function Write-TextFile([string]$path, [string]$content) {
  $dir = Split-Path -Parent $path
  Ensure-Dir $dir
  $content | Set-Content -Path $path -Encoding UTF8 -NoNewline
}

function Backup-File([string]$path) {
  if (-not (Test-Path $path)) { return }
  $ts = Get-Date -Format "yyyyMMdd_HHmmss"
  Copy-Item -Path $path -Destination ($path + ".bak_" + $ts) -Force
}

function Normalize-Newlines([string]$s) {
  return ($s -replace "`r`n", "`n") -replace "`r", "`n"
}

function Ensure-EntrypointMark-InCmd([string]$cmdPath) {
  if (-not (Test-Path $cmdPath)) { Fail "Entrypoint cmd not found: $cmdPath" }
  $raw = Get-Content -Path $cmdPath -Raw -Encoding UTF8
  $txt = Normalize-Newlines $raw

  if ($txt -match 'set\s+"MOCKA_ENTRYPOINT=run_infield_retry_worker\.cmd"') {
    Info "OK: entry mark already present in $cmdPath"
    return
  }

  Backup-File $cmdPath

  $lines = $txt -split "`n"
  $out = New-Object System.Collections.Generic.List[string]
  $inserted = $false

  for ($i = 0; $i -lt $lines.Count; $i++) {
    $line = $lines[$i]

    if (-not $inserted -and $line -match '^\s*@echo\s+off\s*$') {
      $out.Add($line)
      $out.Add('setlocal')
      $out.Add('')
      $out.Add('rem Canonical entry mark (do not change lightly)')
      $out.Add('set "MOCKA_ENTRYPOINT=run_infield_retry_worker.cmd"')
      $out.Add('')
      $inserted = $true
      continue
    }

    if (-not $inserted -and $line -match '^\s*setlocal\b') {
      $out.Add($line)
      $out.Add('')
      $out.Add('rem Canonical entry mark (do not change lightly)')
      $out.Add('set "MOCKA_ENTRYPOINT=run_infield_retry_worker.cmd"')
      $out.Add('')
      $inserted = $true
      continue
    }

    $out.Add($line)
  }

  if (-not $inserted) {
    $out.Insert(0, '')
    $out.Insert(0, 'set "MOCKA_ENTRYPOINT=run_infield_retry_worker.cmd"')
    $out.Insert(0, 'rem Canonical entry mark (do not change lightly)')
    $out.Insert(0, 'setlocal')
    $out.Insert(0, '@echo off')
  }

  $newTxt = ($out -join "`r`n").TrimEnd() + "`r`n"
  $newTxt | Set-Content -Path $cmdPath -Encoding UTF8 -NoNewline
  Info "OK: entry mark inserted into $cmdPath"
}

# Main
$root = (Resolve-Path $RepoRoot).Path
Info "RepoRoot: $root"

# Ensure docs/ops exist (do not overwrite existing content here)
Ensure-Dir (Join-Path $root "docs")
Ensure-Dir (Join-Path $root "ops")

# Ensure entry mark
$cmdPath = Join-Path $root $EntrypointCmd
Ensure-EntrypointMark-InCmd $cmdPath

Info "DONE"
Info "Next: powershell -ExecutionPolicy Bypass -File ops\check_infield.ps1 -RepoRoot ."