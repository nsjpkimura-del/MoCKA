# C:\Users\sirok\MoCKA\audit\ed25519\governance\impact_registry_append_phase14_completion.py
# note: Phase14.6 institutional completion document registry (chain-safe version)

import os
import csv
import sqlite3
from datetime import datetime, timezone

ROOT = r"C:\Users\sirok\MoCKA"
CSV_PATH = os.path.join(ROOT, "audit", "ed25519", "governance", "impact_registry.csv")
DOC_PATH = os.path.join(ROOT, "docs", "PHASE14.6_DUAL_LAYER_GOVERNANCE_COMPLETION.md")
DB_PATH = os.path.join(ROOT, "audit", "ed25519", "governance", "governance.db")

def get_latest_tip():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # governance の最新 TIP は prev_event_id に参照されていない event
    cur.execute("""
        SELECT event_id
        FROM governance_ledger_event
        WHERE event_id NOT IN (
            SELECT prev_event_id FROM governance_ledger_event
        )
        LIMIT 1;
    """)
    row = cur.fetchone()
    conn.close()

    if not row:
        raise RuntimeError("TIP_NOT_FOUND")

    return row[0]

def main():
    tip = get_latest_tip()
    now = datetime.now(timezone.utc).isoformat()

    row = [
        now,
        "phase14_6_completion",
        DOC_PATH,
        "institutional_record",
        tip,
        "note: Phase14.6 completion document sealed and TIP-anchored"
    ]

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)

    print("OK: impact_registry appended (completion document)")
    print("TIP_EVENT_ID:", tip)

if __name__ == "__main__":
    main()