param(
  [string]$Outbox = "C:\Users\sirok\MoCKA\outbox",
  [switch]$EnableNetwork,
  [int]$TimeoutSec = 10
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Ensure-Dir([string]$p){
  if(-not (Test-Path $p)){ New-Item -ItemType Directory -Path $p -Force | Out-Null }
}

function EnvVal([string]$name){
  $v = [Environment]::GetEnvironmentVariable($name, "Process")
  if([string]::IsNullOrEmpty($v)){ $v = [Environment]::GetEnvironmentVariable($name, "User") }
  if([string]::IsNullOrEmpty($v)){ $v = [Environment]::GetEnvironmentVariable($name, "Machine") }
  return $v
}

function Mask([string]$s){
  if([string]::IsNullOrEmpty($s)){ return $null }
  if($s.Length -le 8){ return ("*" * $s.Length) }
  return ($s.Substring(0,4) + "..." + $s.Substring($s.Length-4,4))
}

function Test-Http([string]$name, [string]$url, [hashtable]$headers, [int]$timeoutSec){
  $r = [pscustomobject]@{ name=$name; url=$url; ok=$false; status=$null; error=$null }
  try{
    $resp = Invoke-WebRequest -Uri $url -Headers $headers -Method GET -TimeoutSec $timeoutSec -UseBasicParsing
    $r.status = $resp.StatusCode
    $r.ok = ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500)
  } catch {
    # Try to extract status code if present
    $msg = $_.Exception.Message
    $r.error = $msg
    try{
      if($_.Exception.Response -and $_.Exception.Response.StatusCode){
        $r.status = [int]$_.Exception.Response.StatusCode
      }
    } catch { }
    $r.ok = $false
  }
  return $r
}

Ensure-Dir $Outbox
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$healthPath = Join-Path $Outbox ("health_{0}.json" -f $ts)
$proofPath  = Join-Path $Outbox ("integrity_proof_health_{0}.json" -f $ts)

# Key presence checks (no network)
$openaiKey   = EnvVal "OPENAI_API_KEY"
$githubToken = EnvVal "GITHUB_TOKEN"
$firebaseKey = EnvVal "FIREBASE_API_KEY"

$keyStatus = @(
  [pscustomobject]@{ name="openai";    present=(-not [string]::IsNullOrEmpty($openaiKey));   masked=(Mask $openaiKey) },
  [pscustomobject]@{ name="github";   present=(-not [string]::IsNullOrEmpty($githubToken)); masked=(Mask $githubToken) },
  [pscustomobject]@{ name="firebase"; present=(-not [string]::IsNullOrEmpty($firebaseKey)); masked=(Mask $firebaseKey) }
)

# Optional network checks (explicit opt-in)
$netChecks = @()
if($EnableNetwork){
  if(-not [string]::IsNullOrEmpty($openaiKey)){
    $netChecks += (Test-Http "openai" "https://api.openai.com/v1/models" @{ Authorization=("Bearer " + $openaiKey) } $TimeoutSec)
  } else {
    $netChecks += [pscustomobject]@{ name="openai"; url="https://api.openai.com/v1/models"; ok=$false; status=$null; error="missing key" }
  }

  if(-not [string]::IsNullOrEmpty($githubToken)){
    $netChecks += (Test-Http "github" "https://api.github.com/user" @{ Authorization=("Bearer " + $githubToken); "User-Agent"="mocka-healthcheck" } $TimeoutSec)
  } else {
    $netChecks += [pscustomobject]@{ name="github"; url="https://api.github.com/user"; ok=$false; status=$null; error="missing token" }
  }

  # Firebase is ambiguous without project; only presence is recorded by default
  if(-not [string]::IsNullOrEmpty($firebaseKey)){
    $netChecks += [pscustomobject]@{ name="firebase"; url=$null; ok=$true; status=$null; error="network check not configured" }
  } else {
    $netChecks += [pscustomobject]@{ name="firebase"; url=$null; ok=$false; status=$null; error="missing key" }
  }
}

# Derive mode
# - If network disabled: NORMAL if at least one key present; DEGRADED if none
# - If network enabled: NORMAL if all enabled checks ok; DEGRADED if some ok; ISOLATED if none ok
$mode = "UNKNOWN"
if(-not $EnableNetwork){
  $presentCount = @($keyStatus | Where-Object { $_.present }).Count
  if($presentCount -gt 0){ $mode = "NORMAL" } else { $mode = "DEGRADED" }
} else {
  $okCount = @($netChecks | Where-Object { $_.ok }).Count
  if($okCount -eq 0){ $mode = "ISOLATED" }
  elseif($okCount -lt $netChecks.Count){ $mode = "DEGRADED" }
  else { $mode = "NORMAL" }
}

$healthObj = [pscustomobject]@{
  ts_local = (Get-Date -Format o)
  ts_utc   = ([DateTime]::UtcNow.ToString("o"))
  kind = "health_summary"
  enable_network = [bool]$EnableNetwork
  mode = $mode
  key_status = $keyStatus
  network_checks = $netChecks
}

$healthObj | ConvertTo-Json -Depth 8 | Set-Content -Path $healthPath -Encoding UTF8 -NoNewline

$proofObj = [pscustomobject]@{
  ts = (Get-Date -Format o)
  kind = "integrity_proof"
  artifacts = @(
    @{ path = $healthPath; sha256 = (Get-FileHash $healthPath -Algorithm SHA256).Hash }
  )
}
$proofObj | ConvertTo-Json -Depth 6 | Set-Content -Path $proofPath -Encoding UTF8 -NoNewline

Write-Host ("Wrote: " + $healthPath)
Write-Host ("Wrote: " + $proofPath)
