param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("save","batch","search","get","getbatch")]
    [string]$mode,

    [string]$text,
    [string]$query,
    [string[]]$id
)

# ===== 基本設定 =====
$base = "C:\Users\sirok\MoCKA\infield\phase11"
$python = "python"

Set-Location $base

# ===== SAVE =====
if ($mode -eq "save") {

    if (-not $text) {
        Write-Host "Usage: -mode save -text `"your text`""
        exit 1
    }

    & $python gateway_save_fast.py --raw_text "$text"
    exit
}

# ===== BATCH SAVE =====
if ($mode -eq "batch") {

    & $python gateway_save_batch.py
    exit
}

# ===== SEARCH =====
if ($mode -eq "search") {

    if (-not $query) {
        Write-Host "Usage: -mode search -query `"your query`""
        exit 1
    }

    & $python gateway_search_fast.py --query "$query"
    exit
}

# ===== GET SINGLE =====
if ($mode -eq "get") {

    if (-not $id) {
        Write-Host "Usage: -mode get -id <sha>"
        exit 1
    }

    & $python gateway_get.py $id[0]
    exit
}

# ===== GET BATCH =====
if ($mode -eq "getbatch") {

    if (-not $id) {
        Write-Host "Usage: -mode getbatch -id id1 id2 id3"
        exit 1
    }

    & $python gateway_get_batch.py $id
    exit
}

Write-Host "Invalid mode."
exit 1
