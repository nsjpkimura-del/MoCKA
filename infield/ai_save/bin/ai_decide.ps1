param(
  [Parameter(Mandatory=$true)][string]$Scope,
  [Parameter(Mandatory=$true)][string]$Decision,
  [Parameter(Mandatory=$true)][string]$Reason,
  [Parameter(Mandatory=$true)][string]$ChangeSummary,
  [string]$Refs = "",
  [string]$Actor = $env:USERNAME
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Csv = Join-Path (Join-Path (Split-Path -Parent $PSScriptRoot) "decisions") "decisions.csv"
if(!(Test-Path $Csv)){
  "ts_iso,dec_id,scope,decision,reason,change_summary,actor,refs" | Set-Content -Encoding UTF8 $Csv
}

$ts = Get-Date
$tsIso = $ts.ToString("yyyy-MM-ddTHH:mm:ss.fffK")
$stamp = $ts.ToString("yyyyMMdd_HHmmss")
$DecId = "DC-$stamp"

function CsvEscape([string]$s){
  if($null -eq $s){ return "" }
  $s2 = $s.Replace('"','""')
  if($s2 -match "[,`r`n]"){ return '"' + $s2 + '"' }
  return $s2
}

$row = @(
  (CsvEscape $tsIso),
  (CsvEscape $DecId),
  (CsvEscape $Scope),
  (CsvEscape $Decision),
  (CsvEscape $Reason),
  (CsvEscape $ChangeSummary),
  (CsvEscape $Actor),
  (CsvEscape $Refs)
) -join ","

Add-Content -Encoding UTF8 -Path $Csv -Value $row

Write-Output $DecId
Write-Output $Csv
