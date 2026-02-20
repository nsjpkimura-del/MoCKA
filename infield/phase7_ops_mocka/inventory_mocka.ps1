param(
  [string]$Base = "C:\Users\sirok",
  [string[]]$Roots = @(
    "C:\Users\sirok\ops_mocka",
    "C:\Users\sirok\ops",
    "C:\Users\sirok\docs"
  ),
  [string]$Outbox = "C:\Users\sirok\MoCKA\outbox",
  [int]$TreeDepth = 3,
  [int]$TopFilesMd = 300,
  [int]$TopHitsJson = 200
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Ensure-Dir([string]$p){
  if(-not (Test-Path $p)){
    New-Item -ItemType Directory -Force -Path $p | Out-Null
  }
}

function BytesToHuman([long]$b){
  if($b -ge 1TB){ "{0:N2} TB" -f ($b/1TB) }
  elseif($b -ge 1GB){ "{0:N2} GB" -f ($b/1GB) }
  elseif($b -ge 1MB){ "{0:N2} MB" -f ($b/1MB) }
  elseif($b -ge 1KB){ "{0:N2} KB" -f ($b/1KB) }
  else { "$b B" }
}

function Safe-GetChildFiles([string]$root, [string]$filter){
  @(Get-ChildItem -Path $root -Recurse -Force -File -Filter $filter -ErrorAction SilentlyContinue)
}

function Get-DirSummary([string]$p){
  if(-not (Test-Path $p)){
    return [pscustomobject]@{ Path=$p; Exists=$false; Files=0; Bytes=0; LastWriteTime=$null }
  }
  $files = @(Get-ChildItem -Path $p -Recurse -Force -File -ErrorAction SilentlyContinue)
  $bytes = ($files | Measure-Object -Property Length -Sum).Sum
  $last = ($files | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
  [pscustomobject]@{
    Path = $p
    Exists = $true
    Files = $files.Count
    Bytes = [long]$bytes
    LastWriteTime = $last
  }
}

function Get-TreeText([string]$root, [int]$depth){
  $indent = "  "
  $sb = New-Object System.Text.StringBuilder

  function Walk([string]$dir, [int]$d, [string]$prefix){
    if($d -lt 0){ return }

    $items = @(Get-ChildItem -Path $dir -Force -ErrorAction SilentlyContinue |
      Where-Object {
        $_.Name -notin @(".git",".venv","venv","env","__pycache__","node_modules")
      } |
      Sort-Object @{Expression={-not $_.PSIsContainer}}, Name)

    foreach($it in $items){
      $name = $it.Name
      if($it.PSIsContainer){ $name = $name + "\" }
      [void]$sb.AppendLine($prefix + $name)
      if($it.PSIsContainer){
        Walk $it.FullName ($d - 1) ($prefix + $indent)
      }
    }
  }

  Walk $root $depth ""
  $sb.ToString()
}

function RepoSummary([string]$root){
  $hasGit = Test-Path (Join-Path $root ".git")
  $venvDirs = @(
    Get-ChildItem -Path $root -Recurse -Force -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -in @(".venv","venv","env") } |
    Select-Object -ExpandProperty FullName
  )

  $envFiles = @(
    Get-ChildItem -Path $root -Recurse -Force -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -eq ".env" -or $_.Name -like ".env.*" } |
    Select-Object -ExpandProperty FullName
  )

  $pyManifests = @()
  $pyManifests += @(Get-ChildItem -Path $root -Recurse -Force -File -Filter "pyproject.toml" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
  $pyManifests += @(Get-ChildItem -Path $root -Recurse -Force -File -Filter "requirements*.txt" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
  $pyManifests += @(Get-ChildItem -Path $root -Recurse -Force -File -Filter "poetry.lock" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
  $pyManifests += @(Get-ChildItem -Path $root -Recurse -Force -File -Filter "Pipfile*" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
  $pyManifests = @($pyManifests | Sort-Object -Unique)

  $entrypoints = @()
  $entrypoints += @(Get-ChildItem -Path $root -Recurse -Force -File -Filter "*.ps1" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
  $entrypoints += @(Get-ChildItem -Path $root -Recurse -Force -File -Filter "*.cmd" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
  $entrypoints += @(Get-ChildItem -Path $root -Recurse -Force -File -Filter "*.bat" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
  $entrypoints = @($entrypoints | Sort-Object -Unique)

  [pscustomobject]@{
    Root = $root
    HasGit = [bool]$hasGit
    VenvDirCount = @($venvDirs).Count
    EnvFileCount = @($envFiles).Count
    PythonManifestCount = @($pyManifests).Count
    EntrypointCount = @($entrypoints).Count
  }
}

Ensure-Dir $Outbox
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$mdPath   = Join-Path $Outbox ("inventory_{0}.md" -f $ts)
$jsonPath = Join-Path $Outbox ("inventory_{0}.json" -f $ts)
$proofPath= Join-Path $Outbox ("integrity_proof_inventory_{0}.json" -f $ts)

$generatedLocal = (Get-Date -Format o)
$generatedUtc   = ([DateTime]::UtcNow.ToString("o"))

# Resolve targets:
# - given roots that exist
# - plus mocka-* directories under base
$targets = @()

foreach($r in $Roots){
  if(Test-Path $r){
    $targets += @([pscustomobject]@{ FullName=$r; Name=(Split-Path $r -Leaf) })
  }
}

$mockaDirs = @(Get-ChildItem -Path $Base -Force -Directory -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -like "mocka-*" } |
  Sort-Object Name)

foreach($d in $mockaDirs){
  $targets += @([pscustomobject]@{ FullName=$d.FullName; Name=$d.Name })
}

# Unique by FullName
$targets = @($targets | Sort-Object FullName -Unique)

# Summaries
$dirSummary = @()
foreach($t in $targets){
  $dirSummary += @(Get-DirSummary $t.FullName)
}

# Collect relevant hits
$patterns = @("*.ps1","*.py","*.json","*.yaml","*.yml","*.csv","*.md","*.env","*.toml","*.ini","*.txt")
$all = @()
foreach($t in $targets){
  foreach($pat in $patterns){
    $all += @(Safe-GetChildFiles $t.FullName $pat)
  }
}
$all = @($all | Sort-Object -Unique)

$regex = "mocka|infield|orchestrator|bridge|ledger|registry|phase|constitution|inventory|credential"
$hits = @($all | Where-Object { $_.FullName -match $regex } | Sort-Object LastWriteTime -Descending)

# Build Markdown
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("# MoCKA Inventory Report")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("generated_at_local: " + $generatedLocal)
[void]$sb.AppendLine("generated_at_utc: " + $generatedUtc)
[void]$sb.AppendLine("base: " + $Base)
[void]$sb.AppendLine("outbox: " + $Outbox)
[void]$sb.AppendLine("")

[void]$sb.AppendLine("## Targets")
foreach($t in $targets){
  [void]$sb.AppendLine("- " + $t.FullName)
}
[void]$sb.AppendLine("")

[void]$sb.AppendLine("## Summary")
[void]$sb.AppendLine("| path | exists | files | size | last_write_time |")
[void]$sb.AppendLine("|---|---:|---:|---:|---|")
foreach($s in $dirSummary){
  [void]$sb.AppendLine( ("| {0} | {1} | {2} | {3} | {4} |" -f $s.Path, $s.Exists, $s.Files, (BytesToHuman $s.Bytes), $s.LastWriteTime) )
}
[void]$sb.AppendLine("")

[void]$sb.AppendLine("## Repositories")
foreach($t in $targets){
  $rs = RepoSummary $t.FullName
  [void]$sb.AppendLine("### " + $t.Name)
  [void]$sb.AppendLine("Root: " + $rs.Root)
  [void]$sb.AppendLine("HasGit: " + $rs.HasGit)
  [void]$sb.AppendLine("VenvDirCount: " + $rs.VenvDirCount)
  [void]$sb.AppendLine("EnvFileCount: " + $rs.EnvFileCount)
  [void]$sb.AppendLine("PythonManifestCount: " + $rs.PythonManifestCount)
  [void]$sb.AppendLine("EntrypointCount: " + $rs.EntrypointCount)
  [void]$sb.AppendLine("")
}

[void]$sb.AppendLine("## Trees (trimmed)")
foreach($t in $targets){
  [void]$sb.AppendLine("### " + $t.Name)
  [void]$sb.AppendLine("TREE_START")
  [void]$sb.AppendLine((Get-TreeText $t.FullName $TreeDepth))
  [void]$sb.AppendLine("TREE_END")
  [void]$sb.AppendLine("")
}

[void]$sb.AppendLine("## Relevant Files (top by LastWriteTime)")
[void]$sb.AppendLine("| last_write_time | size | full_name |")
[void]$sb.AppendLine("|---|---:|---|")
foreach($f in ($hits | Select-Object -First $TopFilesMd)){
  [void]$sb.AppendLine( ("| {0} | {1} | {2} |" -f $f.LastWriteTime, (BytesToHuman $f.Length), $f.FullName) )
}
[void]$sb.AppendLine("")

[void]$sb.AppendLine("## Phase 5-7 Placement Skeleton")
[void]$sb.AppendLine("Phase5_root: C:\Users\sirok\docs")
[void]$sb.AppendLine("Phase6_root: C:\Users\sirok\ops")
[void]$sb.AppendLine("Phase7_root: C:\Users\sirok\ops_mocka")
[void]$sb.AppendLine("Note: location fixed, content curation deferred")
[void]$sb.AppendLine("")

# Emit md
$sb.ToString() | Set-Content -Path $mdPath -Encoding UTF8 -NoNewline

# Emit compact json
$jsonTargets = @($dirSummary | Select-Object Path,Exists,Files,Bytes,LastWriteTime)
$jsonHitsTop = @($hits | Select-Object -First $TopHitsJson | Select-Object FullName,Length,LastWriteTime)

$jsonObj = [pscustomobject]@{
  ts_local = (Get-Date -Format o)
  ts_utc = ([DateTime]::UtcNow.ToString("o"))
  kind = "inventory_summary"
  base = $Base
  roots = $Roots
  outbox = $Outbox
  targets = $jsonTargets
  hit_files_top = $jsonHitsTop
}
$jsonObj | ConvertTo-Json -Depth 8 | Set-Content -Path $jsonPath -Encoding UTF8 -NoNewline

# Emit integrity proof (sha256 record)
$proofObj = [pscustomobject]@{
  ts = (Get-Date -Format o)
  kind = "integrity_proof"
  artifacts = @(
    @{ path = $mdPath; sha256 = (Get-FileHash $mdPath -Algorithm SHA256).Hash },
    @{ path = $jsonPath; sha256 = (Get-FileHash $jsonPath -Algorithm SHA256).Hash }
  )
}
$proofObj | ConvertTo-Json -Depth 6 | Set-Content -Path $proofPath -Encoding UTF8 -NoNewline

Write-Host ("Wrote: " + $mdPath)
Write-Host ("Wrote: " + $jsonPath)
Write-Host ("Wrote: " + $proofPath)
