# C:\Users\sirok\MoCKA\audit\ed25519\governance\impact_registry_append_tip.py
# note: Phase14.6 impact_registry append helper (bind latest TIP)

import os
import csv
import sqlite3
from datetime import datetime, timezone

ROOT = r"C:\Users\sirok\MoCKA"
DB_PATH = os.path.join(ROOT, "audit", "ed25519", "governance", "governance.db")
CSV_PATH = os.path.join(ROOT, "audit", "ed25519", "governance", "impact_registry.csv")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def get_tip_event_id() -> str:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT event_id
        FROM governance_ledger_event
        ORDER BY rowid DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    conn.close()
    if not row:
        raise RuntimeError("EMPTY_GOVERNANCE_LEDGER")
    return row[0]

def main():
    tip = get_tip_event_id()
    ts = utc_now_iso()

    scope = "phase14_6"
    artifact_path = r"C:\Users\sirok\MoCKA\audit\ed25519\governance\governance.db"
    impact_level = "info"
    note = "note: Phase14.6 impact_registry append (latest TIP anchored)"

    with open(CSV_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([ts, scope, artifact_path, impact_level, tip, note])

    print("OK: impact_registry appended")
    print("TIP_EVENT_ID:", tip)

if __name__ == "__main__":
    main()