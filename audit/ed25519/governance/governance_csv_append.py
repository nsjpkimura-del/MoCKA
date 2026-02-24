# C:\Users\sirok\MoCKA\audit\ed25519\governance\governance_csv_append.py
# note: Phase14.6 CSV append helper (change_log.csv)

import os
import csv
import sqlite3
from datetime import datetime, timezone

ROOT = r"C:\Users\sirok\MoCKA"
DB_PATH = os.path.join(ROOT, "audit", "ed25519", "governance", "governance.db")
CSV_PATH = os.path.join(ROOT, "audit", "ed25519", "governance", "change_log.csv")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def get_tip() -> tuple[str, str]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT event_id, prev_event_id
        FROM governance_ledger_event
        ORDER BY rowid DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    conn.close()
    if not row:
        raise RuntimeError("EMPTY_GOVERNANCE_LEDGER")
    return row[0], row[1]

def main():
    tip_event_id, tip_prev_id = get_tip()
    ts = utc_now_iso()

    # note: CSVは可読レイヤ。真正性はgovernance.dbで担保される。
    note = "note: Phase14.6 change_log append for latest TIP"

    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    with open(CSV_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([ts, "TIP_UPDATE", tip_event_id, tip_prev_id, note])

    print("OK: change_log appended")
    print("TIP_EVENT_ID:", tip_event_id)

if __name__ == "__main__":
    main()