param(
    [string]$OutputDir = "verify_pack"
)

$ErrorActionPreference = "Stop"

$BaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $BaseDir

$OutputPath = Join-Path $BaseDir $OutputDir

Write-Host "Creating verify pack at $OutputPath"

if (Test-Path $OutputPath) {
    Remove-Item $OutputPath -Recurse -Force
}
New-Item -ItemType Directory -Path $OutputPath | Out-Null

# Required files
$req = @(
    "audit.db",
    ".\keys\ed25519_public.key"
)

foreach ($p in $req) {
    if (-not (Test-Path $p)) {
        Write-Error "Required file missing: $p"
        exit 1
    }
}

# Optional verifier script (copy if exists)
if (Test-Path "verify_full_chain_and_signature.py") {
    Copy-Item "verify_full_chain_and_signature.py" (Join-Path $OutputPath "verify_full_chain_and_signature.py")
}

# Copy artifacts
Copy-Item "audit.db" (Join-Path $OutputPath "audit.db")
Copy-Item ".\keys\ed25519_public.key" (Join-Path $OutputPath "ed25519_public.key")

# Fixed final hash
$FinalHash = "33a71502fde5540eed1939a017410e137e580c583477129313e679096e453f39"
Set-Content -Path (Join-Path $OutputPath "final_chain_hash.txt") -Value $FinalHash -Encoding ASCII

# README
$Readme = @"
External Verification Pack

Files:
- audit.db
- ed25519_public.key
- final_chain_hash.txt
- verify_full_chain_and_signature.py (if included)

Verify:
1) Put this folder on a clean machine.
2) Run:
   python verify_full_chain_and_signature.py

Expected final_chain_hash:
$FinalHash
"@

Set-Content -Path (Join-Path $OutputPath "README.txt") -Value $Readme -Encoding ASCII

Write-Host "Verify pack created successfully."