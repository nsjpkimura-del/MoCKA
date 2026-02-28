param(
  [Parameter(Mandatory=$true)][string]$Title,
  [Parameter(Mandatory=$true)][string]$Summary,
  [string]$Tags = "",
  [ValidateSet("chatgpt","gemini","claude","manual","web","other")][string]$Source = "chatgpt",
  [string]$Actor = $env:USERNAME
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Base = Split-Path -Parent $PSScriptRoot
$Index = Join-Path $Base "index.csv"
$ItemsDir = Join-Path $Base "items"

if(!(Test-Path $ItemsDir)){ New-Item -ItemType Directory -Force -Path $ItemsDir | Out-Null }

$Header = "ts_iso,item_id,title,summary,tags,source,actor,body_path,body_sha256,ext_ref"
if(!(Test-Path $Index)){
  $Header | Set-Content -Encoding UTF8 $Index
} else {
  $first = (Get-Content $Index -TotalCount 1)
  if($first -ne $Header){
    throw "index.csv header mismatch. Refuse to write."
  }
}

$Body = Get-Clipboard -Raw
if([string]::IsNullOrWhiteSpace($Body)){
  throw "Clipboard is empty."
}

$ts = Get-Date
$tsIso = $ts.ToString("yyyy-MM-ddTHH:mm:ss.fffK")
$stamp = $ts.ToString("yyyyMMdd_HHmmss")

$sha = [System.Security.Cryptography.SHA256]::Create()
$bytes = [System.Text.Encoding]::UTF8.GetBytes($Body)
$hash = ($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString("x2") }) -join ""
$hash8 = $hash.Substring(0,8)

$ItemId = "AS-$stamp-$hash8"
$BodyRel = Join-Path "items" ("$ItemId.md")
$BodyPath = Join-Path $Base $BodyRel

$Md = @(
  "# " + $Title,
  "",
  "- item_id: " + $ItemId,
  "- ts_iso: " + $tsIso,
  "- source: " + $Source,
  "- actor: " + $Actor,
  "- tags: " + $Tags,
  "",
  "## Summary",
  $Summary,
  "",
  "## Body",
  "",
  $Body.TrimEnd()
) -join "`r`n"

Set-Content -Encoding UTF8 -Path $BodyPath -Value ($Md + "`r`n")

function CsvEscape([string]$s){
  if($null -eq $s){ return "" }
  $s2 = $s.Replace('"','""')
  if($s2 -match "[,`r`n]"){ return '"' + $s2 + '"' }
  return $s2
}

$ExtRef = ""

$row = @(
  (CsvEscape $tsIso),
  (CsvEscape $ItemId),
  (CsvEscape $Title),
  (CsvEscape $Summary),
  (CsvEscape $Tags),
  (CsvEscape $Source),
  (CsvEscape $Actor),
  (CsvEscape $BodyRel),
  (CsvEscape $hash),
  (CsvEscape $ExtRef)
) -join ","

Add-Content -Encoding UTF8 -Path $Index -Value $row

Write-Output $ItemId
Write-Output $BodyPath
