# C:\Users\sirok\MoCKA\audit\ed25519\governance\init_governance_db.py
# note: Phase14.6 Roadmap-1 governance.db 初期化

import os
import sqlite3
import hashlib
import json
from datetime import datetime, timezone

ROOT = r"C:\Users\sirok\MoCKA"
DB_PATH = os.path.join(ROOT, "audit", "ed25519", "governance", "governance.db")

def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # governance_ledger_event 作成
    cur.execute("""
    CREATE TABLE IF NOT EXISTS governance_ledger_event (
        event_id TEXT PRIMARY KEY,
        prev_event_id TEXT NOT NULL,
        timestamp_utc TEXT NOT NULL,
        event_type TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        note TEXT NOT NULL,
        chain_hash TEXT NOT NULL
    )
    """)

    # 既存件数確認
    cur.execute("SELECT COUNT(*) FROM governance_ledger_event")
    count = cur.fetchone()[0]
    if count > 0:
        print("ALREADY_INITIALIZED")
        return

    # Proof TIP 参照値（Phase14確定TIP）
    proof_tip = "33cedbb94b557e08c1babf10006f288c112e26b2ecd4cb563458ff632f3b07d9"

    timestamp = datetime.now(timezone.utc).isoformat()

    payload = {
        "phase": "14.6",
        "reason": "Dual-Layer Governance Adoption",
        "proof_tip_hash": proof_tip
    }

    payload_json = json.dumps(payload, sort_keys=True)

    genesis_material = (
        "GENESIS" +
        timestamp +
        "GOVERNANCE_GENESIS" +
        payload_json
    ).encode("utf-8")

    event_id = sha256_hex(genesis_material)

    chain_material = (
        event_id +
        "GENESIS"
    ).encode("utf-8")

    chain_hash = sha256_hex(chain_material)

    cur.execute("""
    INSERT INTO governance_ledger_event
    (event_id, prev_event_id, timestamp_utc, event_type, payload_json, note, chain_hash)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id,
        "GENESIS",
        timestamp,
        "GOVERNANCE_GENESIS",
        payload_json,
        "Phase14.6 Roadmap-1 Genesis creation",
        chain_hash
    ))

    conn.commit()
    conn.close()

    print("GOVERNANCE_GENESIS_CREATED")
    print("EVENT_ID:", event_id)
    print("CHAIN_HASH:", chain_hash)

if __name__ == "__main__":
    main()