param(
  [Parameter(Position=0)]
  [string]$Command = "help",

  [Parameter(Position=1)]
  [string]$Arg0 = "",

  [Parameter(Position=2)]
  [string]$Arg1 = "",

  [Parameter(Position=3)]
  [string]$Arg2 = "",

  [Parameter(Position=4)]
  [string]$Arg3 = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Root {
  if (![string]::IsNullOrWhiteSpace($PSScriptRoot)) {
    return $PSScriptRoot
  }
  return (Get-Location).Path
}

function Usage {
  Write-Host ""
  Write-Host "MoCKA Phase11 Runner (Phase11.9.5)"
  Write-Host ""
  Write-Host "Commands:"
  Write-Host "  searchget <query> [top]"
  Write-Host "  backupsearch [file_substring] [top] [hash]"
  Write-Host "  auditsearch [type] [file_substring] [top] [note_substring]"
  Write-Host "  edit <targetFile> <note> [editor]"
  Write-Host "  restore <targetFile> <timestamp>"
  Write-Host ""
}

function RunSearchGet {
  param($query,$top)

  if ([string]::IsNullOrWhiteSpace($query)) { throw "query required" }
  if ($top -le 0) { $top = 20 }

  $py = Join-Path (Root) "gateway_searchget.py"

  Write-Host "RUN: python $py --query $query --top $top"
  & python $py --query $query --top $top
  if ($LASTEXITCODE -ne 0) { throw "searchget failed" }
}

function RunBackupSearch {
  param($fileSub,$top,$withHash)

  if ($top -le 0) { $top = 50 }

  $py = Join-Path (Root) "gateway_backup_search.py"

  $args = @($py,"--top",$top)
  if ($fileSub) { $args += @("--file",$fileSub) }
  if ($withHash) { $args += "--hash" }

  Write-Host ("RUN: python " + ($args -join " "))
  & python @args
  if ($LASTEXITCODE -ne 0) { throw "backupsearch failed" }
}

function RunAuditSearch {
  param($type,$fileSub,$top,$noteSub)

  if (-not $type) { $type = "all" }
  if ($top -le 0) { $top = 50 }

  $py = Join-Path (Root) "gateway_audit_search.py"

  $args = @($py,"--type",$type,"--top",$top)
  if ($fileSub) { $args += @("--file",$fileSub) }
  if ($noteSub) { $args += @("--note",$noteSub) }

  Write-Host ("RUN: python " + ($args -join " "))
  & python @args
  if ($LASTEXITCODE -ne 0) { throw "auditsearch failed" }
}

function RunEdit {
  param($target,$note,$editor)

  if (-not $editor) { $editor = "notepad" }
  if (-not $note) { throw "note required" }

  $safe = Join-Path (Root) "safe_edit.ps1"

  & $safe -TargetFile $target -Editor $editor -Note $note
  if ($LASTEXITCODE -ne 0) { throw "safe_edit failed" }
}

function RunRestore {
  param($target,$timestamp)

  if (-not $timestamp) { throw "timestamp required" }

  $restore = Join-Path (Root) "mocka_restore.ps1"

  & $restore -TargetFile $target -Timestamp $timestamp
  if ($LASTEXITCODE -ne 0) { throw "restore failed" }
}

try {

  $cmd = $Command.ToLowerInvariant()

  switch ($cmd) {

    "help" {
      Usage
      exit 0
    }

    "searchget" {
      RunSearchGet $Arg0 $Arg1
      exit 0
    }

    "backupsearch" {
      $hash = $false
      if ($Arg2 -and $Arg2.ToLowerInvariant() -eq "hash") {
        $hash = $true
      }
      RunBackupSearch $Arg0 $Arg1 $hash
      exit 0
    }

    "auditsearch" {
      RunAuditSearch $Arg0 $Arg1 $Arg2 $Arg3
      exit 0
    }

    "edit" {
      RunEdit $Arg0 $Arg1 $Arg2
      exit 0
    }

    "restore" {
      RunRestore $Arg0 $Arg1
      exit 0
    }

    default {
      Usage
      exit 2
    }
  }

}
catch {
  Write-Host "ERROR:" $_.Exception.Message
  exit 1
}
