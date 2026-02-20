import sqlite3
import hashlib
import json
import sys

DB = r"C:/Users/sirok/MoCKA/audit/ed25519/audit.db"
TABLE = "audit_ledger_event"

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def normalize_json_bytes(text: str) -> bytes:
    obj = json.loads(text)
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")

def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute(f"SELECT id, event_id, prev_chain_hash, chain_hash, event_content FROM {TABLE} ORDER BY id ASC")
    rows = cur.fetchall()

    prev_chain_hash = ""

    for row in rows:
        row_id, event_id, prev_db, chain_db, content = row

        # 1. event_id 再計算
        recalculated_event_id = sha256_hex(normalize_json_bytes(content))
        if recalculated_event_id != event_id:
            raise SystemExit(f"EVENT_ID MISMATCH at id={row_id}")

        # 2. prev_chain_hash 一致確認
        if (prev_db or "") != prev_chain_hash:
            raise SystemExit(f"PREV_CHAIN_HASH MISMATCH at id={row_id}")

        # 3. chain_hash 再計算
        recalculated_chain = sha256_hex((prev_chain_hash + event_id).encode("utf-8"))
        if recalculated_chain != chain_db:
            raise SystemExit(f"CHAIN_HASH MISMATCH at id={row_id}")

        prev_chain_hash = chain_db

    conn.close()

    print(json.dumps({
        "status": "OK",
        "rows_verified": len(rows),
        "final_chain_hash": prev_chain_hash
    }, indent=2))

if __name__ == "__main__":
    main()