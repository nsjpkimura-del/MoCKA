import sqlite3
import hashlib
import json
import re
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

DB = r"C:/Users/sirok/MoCKA/audit/ed25519/audit.db"
TABLE = "audit_ledger_event"
PUBKEY_PATH = r"C:/Users/sirok/MoCKA/audit/ed25519/keys/ed25519_public.key"

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def normalize_json_bytes(text: str) -> bytes:
    obj = json.loads(text)
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")

def load_ed25519_public_key_auto(path: str) -> ed25519.Ed25519PublicKey:
    data = open(path, "rb").read()

    # 1) raw 32 bytes
    if len(data) == 32:
        return ed25519.Ed25519PublicKey.from_public_bytes(data)

    # 2) PEM
    if data.lstrip().startswith(b"-----BEGIN"):
        key = serialization.load_pem_public_key(data)
        if not isinstance(key, ed25519.Ed25519PublicKey):
            raise SystemExit("PUBKEY TYPE MISMATCH: not Ed25519")
        return key

    # 3) text hex (64 hex chars)
    try:
        txt = data.decode("utf-8").strip()
        txt_compact = re.sub(r"\s+", "", txt)
        if re.fullmatch(r"[0-9a-fA-F]{64}", txt_compact):
            return ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(txt_compact))
    except Exception:
        pass

    raise SystemExit(f"PUBKEY FORMAT UNKNOWN: bytes={len(data)} path={path}")

def verify_signature(pubkey: ed25519.Ed25519PublicKey, message_bytes: bytes, signature_hex: str):
    sig = bytes.fromhex(signature_hex)
    pubkey.verify(sig, message_bytes)

def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute(f"SELECT id, event_type, event_id, prev_chain_hash, chain_hash, event_content FROM {TABLE} ORDER BY id ASC")
    rows = cur.fetchall()

    prev_chain_hash = ""
    pubkey = load_ed25519_public_key_auto(PUBKEY_PATH)

    sig_checked = 0

    for row in rows:
        row_id, event_type, event_id, prev_db, chain_db, content = row

        recalculated_event_id = sha256_hex(normalize_json_bytes(content))
        if recalculated_event_id != event_id:
            raise SystemExit(f"EVENT_ID MISMATCH at id={row_id}")

        if (prev_db or "") != prev_chain_hash:
            raise SystemExit(f"PREV_CHAIN_HASH MISMATCH at id={row_id}")

        recalculated_chain = sha256_hex((prev_chain_hash + event_id).encode("utf-8"))
        if recalculated_chain != chain_db:
            raise SystemExit(f"CHAIN_HASH MISMATCH at id={row_id}")

        if event_type == "daily_signature":
            payload = json.loads(content)
            message = payload["message_canonical"].encode("utf-8")
            signature_hex = payload["signature_hex"]
            try:
                verify_signature(pubkey, message, signature_hex)
                sig_checked += 1
            except Exception:
                raise SystemExit(f"SIGNATURE VERIFY FAIL at id={row_id}")

        prev_chain_hash = chain_db

    conn.close()

    print(json.dumps({
        "status": "OK",
        "rows_verified": len(rows),
        "final_chain_hash": prev_chain_hash,
        "signature_checked": sig_checked
    }, indent=2))

if __name__ == "__main__":
    main()