param(
    [string]$EmitPath = "infield/ai_save/phase2/emit_ledger.csv",
    [string]$AcceptPath = "infield/ai_save/phase2/accept_ledger.csv"
)

$emit = Import-Csv $EmitPath
$accept = Import-Csv $AcceptPath

foreach($e in $emit){
    $a = $accept | Where-Object { $_.emit_id -eq $e.emit_id }
    if(-not $a){ throw "HALT: missing accept record for $($e.emit_id)" }
    if($a.received_sha256 -ne $e.payload_sha256){
        throw "HALT: hash mismatch for $($e.emit_id)"
    }
    if($a.match_flag -ne "true"){
        throw "HALT: match_flag false for $($e.emit_id)"
    }
}

Write-Host "JOINT INTEGRITY OK"