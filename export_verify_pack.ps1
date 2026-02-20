param(
  [string]$Root = "C:\Users\sirok\MoCKA",
  [string]$OutDirRel = "outbox\verify_pack",
  [switch]$NoSelfTest
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail([string]$msg){
  Write-Error $msg
  exit 1
}

function Normalize-FullPath([string]$p){
  return [System.IO.Path]::GetFullPath($p)
}

function Assert-UnderRoot([string]$rootAbs, [string]$targetPath){
  $t = Normalize-FullPath $targetPath
  $r = Normalize-FullPath $rootAbs
  if (-not $t.StartsWith($r, [System.StringComparison]::OrdinalIgnoreCase)){
    Fail ("PATH VIOLATION: target is outside root.`nRoot: {0}`nTarget: {1}" -f $r, $t)
  }
}

function Ensure-Dir([string]$rootAbs, [string]$dirPath){
  Assert-UnderRoot $rootAbs $dirPath
  if (Test-Path -LiteralPath $dirPath -PathType Container) { return }
  $parent = Split-Path -Parent $dirPath
  if ([string]::IsNullOrWhiteSpace($parent)) { Fail "INVALID DIR: no parent" }
  $parentAbs = Normalize-FullPath $parent
  $rootAbsN = Normalize-FullPath $rootAbs
  if (-not $parentAbs.StartsWith($rootAbsN, [System.StringComparison]::OrdinalIgnoreCase)){
    Fail ("PATH VIOLATION: parent of {0} is outside root.`nRoot: {1}`nParent: {2}" -f (Normalize-FullPath $dirPath), $rootAbsN, $parentAbs)
  }
  New-Item -ItemType Directory -Path $dirPath -Force | Out-Null
}

function Copy-File-Checked([string]$rootAbs, [string]$src, [string]$dst){
  Assert-UnderRoot $rootAbs $src
  Assert-UnderRoot $rootAbs $dst
  if (-not (Test-Path -LiteralPath $src -PathType Leaf)){
    Fail ("MISSING FILE: {0}" -f (Normalize-FullPath $src))
  }
  $dstParent = Split-Path -Parent $dst
  Ensure-Dir $rootAbs $dstParent
  Copy-Item -LiteralPath $src -Destination $dst -Force
}

function Sha256-File([string]$path){
  return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower()
}

function Write-TextUtf8NoBom([string]$path, [string]$text){
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($path, $text, $utf8NoBom)
}

$rootAbs = Normalize-FullPath $Root
if (-not (Test-Path -LiteralPath $rootAbs -PathType Container)){
  Fail ("ROOT NOT FOUND: {0}" -f $rootAbs)
}

$canonPath = Join-Path $rootAbs "config\phase12_audit_canonical.json"
if (-not (Test-Path -LiteralPath $canonPath -PathType Leaf)){
  Fail ("MISSING CANONICAL JSON: {0}" -f (Normalize-FullPath $canonPath))
}

# Load canonical (BOM tolerant)
$canonText = Get-Content -LiteralPath $canonPath -Raw
$canonText = $canonText.TrimStart([char]0xFEFF)
$canon = $canonText | ConvertFrom-Json

$auditDb = $canon.authoritative_audit_db
if ([string]::IsNullOrWhiteSpace($auditDb)){ Fail "canonical.authoritative_audit_db is empty" }

$pubKey = Join-Path $rootAbs "audit\ed25519\keys\ed25519_public.key"

# Files to include (sources in MoCKA root)
$items = @(
  @{ src = (Join-Path $rootAbs "audit\ed25519\audit.db");                         rel = "audit\ed25519\audit.db" },
  @{ src = $pubKey;                                                              rel = "audit\ed25519\keys\ed25519_public.key" },
  @{ src = $canonPath;                                                           rel = "config\phase12_audit_canonical.json" },
  @{ src = (Join-Path $rootAbs "verify_full_chain.py");                          rel = "verify_full_chain.py" },
  @{ src = (Join-Path $rootAbs "verify_full_chain_and_signature.py");            rel = "verify_full_chain_and_signature.py" },
  @{ src = (Join-Path $rootAbs "README_verify.txt");                             rel = "README_verify.txt" },
  @{ src = (Join-Path $rootAbs "verify.bat");                                    rel = "verify.bat" }
)

# Prepare output dirs
$outDir = Join-Path $rootAbs $OutDirRel
Ensure-Dir $rootAbs $outDir

$ts = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
$stage = Join-Path $outDir ("stage_" + $ts)
Ensure-Dir $rootAbs $stage

# Copy files into stage
foreach($it in $items){
  $dst = Join-Path $stage $it.rel
  Copy-File-Checked $rootAbs $it.src $dst
}

# Create manifest
$manifestLines = New-Object System.Collections.Generic.List[string]
$allFiles = Get-ChildItem -LiteralPath $stage -Recurse -File | Sort-Object FullName
foreach($f in $allFiles){
  $hash = Sha256-File $f.FullName
  $relPath = $f.FullName.Substring($stage.Length).TrimStart("\","/") -replace "/", "\"
  $manifestLines.Add(("{0}  {1}" -f $hash, $relPath))
}
$manifestPath = Join-Path $stage "manifest.sha256.txt"
Write-TextUtf8NoBom $manifestPath ($manifestLines -join "`n")

# Optional self-test inside stage (uses local files)
if (-not $NoSelfTest){
  $py = Join-Path $rootAbs "venv\Scripts\python.exe"
  if (-not (Test-Path -LiteralPath $py -PathType Leaf)){
    Fail ("MISSING venv python: {0}" -f (Normalize-FullPath $py))
  }

  Push-Location $stage
  try{
    & $py ".\verify_full_chain.py" | Out-Host
    if ($LASTEXITCODE -ne 0){ Fail "SELFTEST FAIL: verify_full_chain.py" }

    & $py ".\verify_full_chain_and_signature.py" | Out-Host
    if ($LASTEXITCODE -ne 0){ Fail "SELFTEST FAIL: verify_full_chain_and_signature.py" }
  }
  finally{
    Pop-Location
  }
}

# Zip
$zipName = ("mocka_phase12_verify_{0}.zip" -f $ts)
$zipPath = Join-Path $outDir $zipName
if (Test-Path -LiteralPath $zipPath -PathType Leaf){
  Fail ("REFUSE OVERWRITE: {0}" -f (Normalize-FullPath $zipPath))
}

Compress-Archive -LiteralPath (Join-Path $stage "*") -DestinationPath $zipPath -Force

Write-Host ("OK: verify pack created")
Write-Host ("ZIP:   " + (Normalize-FullPath $zipPath))
Write-Host ("STAGE: " + (Normalize-FullPath $stage))