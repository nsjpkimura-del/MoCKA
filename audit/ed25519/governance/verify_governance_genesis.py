# C:\Users\sirok\MoCKA\audit\ed25519\governance\verify_governance_genesis.py
# note: Phase14.6 Roadmap-1 GENESIS existence verification

import os
import sqlite3

ROOT = r"C:\Users\sirok\MoCKA"
DB_PATH = os.path.join(ROOT, "audit", "ed25519", "governance", "governance.db")

def main():
    if not os.path.exists(DB_PATH):
        print("DB_NOT_FOUND")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT event_id, event_type, prev_event_id, chain_hash
        FROM governance_ledger_event
    """)

    rows = cur.fetchall()
    conn.close()

    print("ROW_COUNT:", len(rows))

    for r in rows:
        print("EVENT_ID:", r[0])
        print("TYPE:", r[1])
        print("PREV:", r[2])
        print("CHAIN_HASH:", r[3])
        print("----")

if __name__ == "__main__":
    main()