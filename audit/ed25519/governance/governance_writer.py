# C:\Users\sirok\MoCKA\audit\ed25519\governance\governance_writer.py
# note: Phase14.6 Roadmap-2 Governance Ledger Writer (append-only)

import os
import sqlite3
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, Tuple

ROOT = r"C:\Users\sirok\MoCKA"
DB_PATH = os.path.join(ROOT, "audit", "ed25519", "governance", "governance.db")

def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def open_db() -> sqlite3.Connection:
    if not os.path.exists(DB_PATH):
        raise RuntimeError("governance.db not found: " + DB_PATH)
    return sqlite3.connect(DB_PATH)

def get_tip(cur: sqlite3.Cursor) -> Tuple[str, str]:
    cur.execute("""
        SELECT event_id, chain_hash
        FROM governance_ledger_event
        ORDER BY rowid DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    if not row:
        raise RuntimeError("governance ledger empty")
    return row[0], row[1]

def append_event(event_type: str, payload: Dict[str, Any], note: str) -> str:
    ts = utc_now_iso()
    payload_json = json.dumps(payload, sort_keys=True, ensure_ascii=True)

    conn = open_db()
    cur = conn.cursor()

    prev_event_id, prev_chain_hash = get_tip(cur)

    material = (
        prev_event_id +
        ts +
        event_type +
        payload_json +
        note
    ).encode("utf-8")

    event_id = sha256_hex(material)

    chain_material = (
        prev_chain_hash +
        event_id +
        prev_event_id
    ).encode("utf-8")

    chain_hash = sha256_hex(chain_material)

    cur.execute("""
        INSERT INTO governance_ledger_event
        (event_id, prev_event_id, timestamp_utc, event_type, payload_json, note, chain_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id,
        prev_event_id,
        ts,
        event_type,
        payload_json,
        note,
        chain_hash
    ))

    conn.commit()
    conn.close()
    return event_id

def main():
    payload = {
        "from_phase": "14",
        "to_phase": "14.6",
        "model": "Dual-Layer Governance Architecture"
    }
    note = "note: Phase14.6 PHASE_TRANSITION recorded (Roadmap-2 smoke)"
    event_id = append_event("PHASE_TRANSITION", payload, note)
    print("OK: appended PHASE_TRANSITION")
    print("EVENT_ID:", event_id)

if __name__ == "__main__":
    main()