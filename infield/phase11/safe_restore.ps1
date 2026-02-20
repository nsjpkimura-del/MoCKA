param(
    [Parameter(Mandatory=$true)]
    [string]$EditJson
)

$ErrorActionPreference = "Stop"

$outbox = "C:\Users\sirok\MoCKA\outbox"

# 絶対パスならそのまま使う
if ([System.IO.Path]::IsPathRooted($EditJson)) {
    $editPath = $EditJson
} else {
    $editPath = Join-Path "C:\Users\sirok\MoCKA" $EditJson
}

if (!(Test-Path $editPath)) {
    throw "Edit JSON not found: $editPath"
}

$edit = Get-Content -Raw -Encoding UTF8 $editPath | ConvertFrom-Json

if (!(Test-Path $edit.backup_path)) {
    throw "Backup file missing: $($edit.backup_path)"
}

Copy-Item $edit.backup_path $edit.target_path -Force

$afterHash = (Get-FileHash $edit.target_path -Algorithm SHA256).Hash.ToLower()

$ts = (Get-Date).ToString("yyyyMMdd_HHmmss")
$id = [guid]::NewGuid().ToString("n")

$outFile = Join-Path $outbox "file_restore_${ts}.json"

$data = @{
    schema = "mocka.phase11.file_restore.v1"
    id = $id
    ts_local = (Get-Date).ToString("o")
    source_edit_outbox = $editPath
    target_path = $edit.target_path
    sha256_source_expected = $edit.sha256_source
    sha256_after = $afterHash
    restore_verified = ($afterHash -eq $edit.sha256_source)
}

$data | ConvertTo-Json -Depth 5 | Set-Content -Path $outFile -Encoding UTF8

Write-Host "OK: $outFile"