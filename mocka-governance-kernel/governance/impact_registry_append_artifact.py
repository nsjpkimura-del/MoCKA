# C:\Users\sirok\MoCKA\audit\ed25519\governance\impact_registry_append_artifact.py
# note: Phase14.6 impact_registry append helper (arbitrary artifact, bind latest TIP)

import os
import csv
import sys
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

def usage() -> int:
    print("USAGE:")
    print("  python impact_registry_append_artifact.py ARTIFACT_PATH SCOPE IMPACT_LEVEL")
    print("EXAMPLE:")
    print(r"  python impact_registry_append_artifact.py .\audit\ed25519\quarantine\X.json phase14_6_quarantine evidence")
    return 2

def main(argv) -> int:
    if len(argv) < 4:
        return usage()

    artifact_path = argv[1]
    scope = argv[2]
    impact_level = argv[3]

    if not os.path.isabs(artifact_path):
        artifact_path = os.path.join(ROOT, artifact_path)

    if not os.path.exists(artifact_path):
        print("FILE_NOT_FOUND:", artifact_path)
        return 2

    tip = get_tip_event_id()
    ts = utc_now_iso()

    note = "note: Phase14.6 impact_registry append (artifact bound to latest TIP)"

    with open(CSV_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([ts, scope, artifact_path, impact_level, tip, note])

    print("OK: impact_registry appended")
    print("TIP_EVENT_ID:", tip)
    print("ARTIFACT:", artifact_path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))