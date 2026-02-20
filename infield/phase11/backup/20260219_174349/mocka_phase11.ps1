param(
  [Parameter(Position=0)]
  [string]$Command = "help",

  [Parameter(Position=1)]
  [string]$TargetFile = "",

  [Parameter(Position=2)]
  [string]$Arg1 = "",

  [Parameter(Position=3)]
  [string]$Arg2 = "",

  [Parameter(Position=4)]
  [string]$Arg3 = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Usage {
  Write-Host ""
  Write-Host "MoCKA Phase11 Runner (Phase11.8 gate integrated)"
  Write-Host ""
  Write-Host "Usage:"
  Write-Host "  cd C:\Users\sirok\MoCKA\infield\phase11"
  Write-Host "  .\mocka_phase11.ps1 help"
  Write-Host ""
  Write-Host "Commands:"
  Write-Host "  searchget <query> [top]"
  Write-Host "  edit <targetFile> <note> [editor]"
  Write-Host "  restore <targetFile> <timestamp>"
  Write-Host ""
  Write-Host "Examples:"
  Write-Host "  .\mocka_phase11.ps1 searchget ""tag:phase11"" 20"
  Write-Host "  .\mocka_phase11.ps1 edit .\gateway_searchget.py ""修正理由"" notepad"
  Write-Host "  .\mocka_phase11.ps1 restore .\gateway_searchget.py 20260219_173105"
  Write-Host ""
}

function Resolve-Phase11Root {
  $here = Split-Path -Parent $MyInvocation.MyCommand.Path
  return $here
}

function Assert-FileExists([string]$Path) {
  if ([string]::IsNullOrWhiteSpace($Path)) {
    throw "TargetFile is required."
  }
  if (!(Test-Path -LiteralPath $Path)) {
    throw "File not found: $Path"
  }
}

function Assert-ToolExists([string]$ToolPath, [string]$Name) {
  if (!(Test-Path -LiteralPath $ToolPath)) {
    throw "Required tool missing: $Name ($ToolPath)"
  }
}

function Run-SearchGet([string]$Query, [int]$Top) {
  $root = Resolve-Phase11Root
  $py = Join-Path $root "gateway_searchget.py"
  if (!(Test-Path -LiteralPath $py)) { throw "gateway_searchget.py not found: $py" }

  if ([string]::IsNullOrWhiteSpace($Query)) { throw "query is required." }
  if ($Top -le 0) { $Top = 20 }

  Write-Host ("RUN: python " + $py + " --query " + $Query + " --top " + $Top)
  & python $py --query $Query --top $Top
  if ($LASTEXITCODE -ne 0) { throw "searchget failed with exitcode=$LASTEXITCODE" }
}

function Run-SafeEdit([string]$Target, [string]$Editor, [string]$Note) {
  $root = Resolve-Phase11Root
  $safe = Join-Path $root "safe_edit.ps1"
  Assert-ToolExists $safe "safe_edit.ps1"
  Assert-FileExists $Target
  if ([string]::IsNullOrWhiteSpace($Note)) { throw "note is required (audit reason)." }

  if ([string]::IsNullOrWhiteSpace($Editor)) {
    $Editor = "notepad"
  }

  Write-Host "SAFE_EDIT: This will create a backup and an outbox file_edit log."
  Write-Host ("  target=" + $Target)
  Write-Host ("  editor=" + $Editor)
  Write-Host ("  note=" + $Note)

  & $safe -TargetFile $Target -Editor $Editor -Note $Note
  if ($LASTEXITCODE -ne 0) { throw "safe_edit failed with exitcode=$LASTEXITCODE" }
}

function Run-Restore([string]$Target, [string]$Timestamp) {
  $root = Resolve-Phase11Root
  $restore = Join-Path $root "mocka_restore.ps1"
  Assert-ToolExists $restore "mocka_restore.ps1"
  Assert-FileExists $Target
  if ([string]::IsNullOrWhiteSpace($Timestamp)) { throw "timestamp is required (YYYYMMDD_HHMMSS)." }

  Write-Host "RESTORE: This will overwrite the target file with the selected backup."
  Write-Host ("  target=" + $Target)
  Write-Host ("  timestamp=" + $Timestamp)

  & $restore -TargetFile $Target -Timestamp $Timestamp
  if ($LASTEXITCODE -ne 0) { throw "restore failed with exitcode=$LASTEXITCODE" }
}

try {
  $cmdRaw = $Command
  if ($null -eq $cmdRaw) { $cmdRaw = "" }
  $cmd = $cmdRaw.ToLowerInvariant()

  switch ($cmd) {
    "help" {
      Write-Usage
      exit 0
    }

    "searchget" {
      $q = $TargetFile
      $top = 20
      if (![string]::IsNullOrWhiteSpace($Arg1)) {
        $top = [int]$Arg1
      }
      Run-SearchGet -Query $q -Top $top
      exit 0
    }

    "edit" {
      $target = $TargetFile
      $note = $Arg1
      $editor = $Arg2
      Run-SafeEdit -Target $target -Editor $editor -Note $note
      exit 0
    }

    "restore" {
      $target = $TargetFile
      $ts = $Arg1
      Run-Restore -Target $target -Timestamp $ts
      exit 0
    }

    default {
      Write-Host ("Unknown command: " + $Command)
      Write-Usage
      exit 2
    }
  }
}
catch {
  Write-Host ("ERROR: " + $_.Exception.Message)
  exit 1
}
