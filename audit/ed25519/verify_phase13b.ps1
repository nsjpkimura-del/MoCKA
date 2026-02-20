param()

$EXPECTED_CHAIN = "e0630325c98603503ac6f2fee954f150afc55b42294f8b15a2130bae62f6f511"
$EXPECTED_VERIFY = "6CD710498943F83A91718918D1F7FF6FC727F3B7FC4BE6D96A9C1CD9E1C296AA"
$EXPECTED_SEAL = "18F1D121E1EDD3D5DFA929CB45B920D4345CEF92AA7718AB781EEA1C6B0342E7"

if (!(Test-Path ".\verify_pack.zip")) { Write-Output "verify_pack.zip missing"; exit 1 }
if (!(Test-Path ".\seal_values.json")) { Write-Output "seal_values.json missing"; exit 1 }

$VERIFY_HASH = (Get-FileHash .\verify_pack.zip -Algorithm SHA256).Hash
$SEAL_HASH = (Get-FileHash .\seal_values.json -Algorithm SHA256).Hash

if ($VERIFY_HASH -ne $EXPECTED_VERIFY) { Write-Output "verify_pack mismatch"; exit 1 }
if ($SEAL_HASH -ne $EXPECTED_SEAL) { Write-Output "seal_values mismatch"; exit 1 }

$seal = Get-Content .\seal_values.json | ConvertFrom-Json

if ($seal.final_chain_hash -ne $EXPECTED_CHAIN) { Write-Output "chain_hash mismatch"; exit 1 }

Write-Output "Phase13-B Verification OK"
exit 0
