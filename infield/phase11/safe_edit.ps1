param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)][string]$Search,
    [Parameter(Mandatory=$true)][string]$Replace
)

$ErrorActionPreference = "Stop"

$root = "C:\Users\sirok\MoCKA"
$outbox = Join-Path $root "outbox"
$backupDir = Join-Path $root "backup"

if (!(Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir | Out-Null
}

$target = Join-Path $root $Path

if (!(Test-Path $target)) { throw "Target not found" }

$content = Get-Content -Raw -Encoding UTF8 $target
$beforeHash = (Get-FileHash $target -Algorithm SHA256).Hash.ToLower()

$newContent = $content.Replace($Search, $Replace)

if ($newContent -eq $content) { throw "No change" }

# === バックアップ保存 ===
$ts = (Get-Date).ToString("yyyyMMdd_HHmmss")
$backupPath = Join-Path $backupDir ("backup_${ts}.bak")
Copy-Item $target $backupPath -Force

# === 編集反映 ===
Set-Content -Path $target -Value $newContent -Encoding UTF8

$afterHash = (Get-FileHash $target -Algorithm SHA256).Hash.ToLower()

$id = [guid]::NewGuid().ToString("n")
$outFile = Join-Path $outbox "file_edit_${ts}.json"

$data = @{
    schema = "mocka.phase11.file_edit.v1"
    id = $id
    ts_local = (Get-Date).ToString("o")
    target_path = $target
    backup_path = $backupPath
    sha256_source = $beforeHash
    sha256_after = $afterHash
}

$data | ConvertTo-Json -Depth 5 | Set-Content -Path $outFile -Encoding UTF8

Write-Host "OK: $outFile"