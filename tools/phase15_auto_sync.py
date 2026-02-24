# C:\Users\sirok\MoCKA\tools\phase15_auto_sync.py
# Phase15 governance->proof reconciliation engine
# mode: audit-only (default)

import sqlite3
import os
import sys

ROOT = r"C:\Users\sirok\MoCKA"
GOV_DB = os.path.join(ROOT, "audit", "ed25519", "governance", "governance.db")
PROOF_DB = os.path.join(ROOT, "audit", "ed25519", "audit.db")

def fetch_governance_decisions():
    conn = sqlite3.connect(GOV_DB)
    cur = conn.cursor()

    cur.execute("""
        SELECT event_id, event_type
        FROM governance_ledger_event
        WHERE event_type IN (
            'CLASSIFICATION_CHANGE_DECISION',
            'QUARANTINE_ACTION_DECISION'
        );
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def main():
    print("=== Phase15 Auto Sync (Audit Mode) ===")

    if not os.path.exists(GOV_DB):
        print("FATAL: governance DB not found")
        sys.exit(2)

    if not os.path.exists(PROOF_DB):
        print("FATAL: proof DB not found")
        sys.exit(3)

    decisions = fetch_governance_decisions()
    print("GOV_DECISION_COUNT:", len(decisions))

    # 現在は照合未実装
    print("STATUS: audit-only mode")
    print("NEXT: implement reconciliation logic")

if __name__ == "__main__":
    main()