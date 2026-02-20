import json
from key_manager import load_private_key, load_public_key

def build_daily_message(date_str, final_chain_hash, file_chain_length, ledger_count):
    payload = {
        "date": date_str,
        "final_chain_hash": final_chain_hash,
        "file_chain_length": int(file_chain_length),
        "ledger_count": int(ledger_count),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")

def sign_daily(date_str, final_chain_hash, file_chain_length, ledger_count):
    private_key = load_private_key()
    msg = build_daily_message(date_str, final_chain_hash, file_chain_length, ledger_count)
    sig = private_key.sign(msg)
    return sig.hex()

def verify_daily(signature_hex, date_str, final_chain_hash, file_chain_length, ledger_count):
    public_key = load_public_key()
    msg = build_daily_message(date_str, final_chain_hash, file_chain_length, ledger_count)
    sig = bytes.fromhex(signature_hex)
    public_key.verify(sig, msg)
    return True