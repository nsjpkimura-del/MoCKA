# C:\Users\sirok\MoCKA\audit\ed25519\governance\backup_index_append_file.py
# note: Phase14.6 backup_index append helper (sha256 file, bind latest TIP)

import os
import csv
import sys
import hashlib
import sqlite3
from datetime import datetime, timezone

ROOT = r"C:\Users\sirok\MoCKA"
DB_PATH = os.path.join(ROOT, "audit", "ed25519", "governance", "governance.db")
CSV_PATH = os.path.join(ROOT, "audit", "ed25519", "governance", "backup_index.csv")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha256_file_hex(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

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
    print("  python backup_index_append_file.py PATH_TO_FILE [BACKUP_ID]")
    print("NOTE:")
    print("  PATH_TO_FILE may be relative to C:\\Users\\sirok\\MoCKA")
    return 2

def main(argv) -> int:
    if len(argv) < 2:
        return usage()

    in_path = argv[1]
    if not os.path.isabs(in_path):
        in_path = os.path.join(ROOT, in_path)

    if not os.path.exists(in_path):
        print("FILE_NOT_FOUND:", in_path)
        return 2

    backup_id = argv[2] if len(argv) >= 3 else ("bk_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))

    digest = sha256_file_hex(in_path)
    tip = get_tip_event_id()
    ts = utc_now_iso()

    note = "note: Phase14.6 backup_index append (sha256 computed, latest TIP anchored)"

    with open(CSV_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([ts, backup_id, in_path, digest, tip, note])

    print("OK: backup_index appended")
    print("BACKUP_ID:", backup_id)
    print("FILE:", in_path)
    print("SHA256:", digest)
    print("TIP_EVENT_ID:", tip)
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))