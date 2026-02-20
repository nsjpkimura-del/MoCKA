param(
  [Parameter(Mandatory=$true)]
  [string]$TargetFile,

  [Parameter(Mandatory=$true)]
  [string]$Timestamp
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Ensure-Dir([string]$p) {
  if (!(Test-Path -LiteralPath $p)) { New-Item -ItemType Directory -Path $p | Out-Null }
}

function Abs-Path([string]$p) {
  return (Resolve-Path -LiteralPath $p).Path
}

function Sha256([string]$p) {
  return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()
}

try {
  if ([string]::IsNullOrWhiteSpace($TargetFile)) { throw "TargetFile is required." }
  if ([string]::IsNullOrWhiteSpace($Timestamp)) { throw "Timestamp is required (YYYYMMDD_HHMMSS)." }

  $phase11Root = Split-Path -Parent $MyInvocation.MyCommand.Path
  $backupDir = Join-Path (Join-Path $phase11Root "backup") $Timestamp

  if (!(Test-Path -LiteralPath $backupDir)) { throw "Backup dir not found: $backupDir" }

  $targetAbs = Abs-Path $TargetFile
  if (!(Test-Path -LiteralPath $targetAbs)) { throw "TargetFile not found: $targetAbs" }

  $fileName = Split-Path -Leaf $targetAbs
  $backupFile = Join-Path $backupDir $fileName
  if (!(Test-Path -LiteralPath $backupFile)) { throw "Backup file not found: $backupFile" }

  Write-Host "RESTORE: this will overwrite target file"
  Write-Host ("  target=" + $targetAbs)
  Write-Host ("  from  =" + $backupFile)

  $preHash = Sha256 $targetAbs
  $srcHash = Sha256 $backupFile

  Copy-Item -LiteralPath $backupFile -Destination $targetAbs -Force

  $postHash = Sha256 $targetAbs

  $outbox = "C:\Users\sirok\MoCKA\outbox"
  Ensure-Dir $outbox
  $logPath = Join-Path $outbox ("file_restore_" + $Timestamp + ".json")

  $log = [ordered]@{
    event_type = "file_restore"
    timestamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
    restore_from_timestamp = $Timestamp
    target = @{
      path = $targetAbs
      file_name = $fileName
      sha256_before = $preHash
      sha256_after = $postHash
    }
    source = @{
      backup_dir = $backupDir
      backup_file = $backupFile
      sha256 = $srcHash
    }
  }

  $log | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $logPath -Encoding UTF8

  Write-Host "RESTORE: done"
  Write-Host ("  sha256_before=" + $preHash)
  Write-Host ("  sha256_source=" + $srcHash)
  Write-Host ("  sha256_after =" + $postHash)
  Write-Host ("  log=" + $logPath)

  exit 0
}
catch {
  Write-Host ("ERROR: " + $_.Exception.Message)
  exit 1
}
