# C:\Users\sirok\MoCKA\audit\ed25519\governance\governance_chain_verify.py
# note: Phase14.6 Roadmap-2 Governance chain verification

import os
import sqlite3
import hashlib
import json

ROOT = r"C:\Users\sirok\MoCKA"
DB_PATH = os.path.join(ROOT, "audit", "ed25519", "governance", "governance.db")

def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def main():
    if not os.path.exists(DB_PATH):
        print("DB_NOT_FOUND")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT event_id, prev_event_id, timestamp_utc, event_type, payload_json, note, chain_hash
        FROM governance_ledger_event
        ORDER BY rowid ASC
    """)
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("EMPTY")
        return

    ok = True

    for i, r in enumerate(rows):
        event_id, prev_event_id, ts, event_type, payload_json, note, chain_hash = r

        if i == 0:
            if prev_event_id != "GENESIS" or event_type != "GOVERNANCE_GENESIS":
                print("FAIL: bad genesis header")
                ok = False
                break
            expected_chain = sha256_hex((event_id + "GENESIS").encode("utf-8"))
            if chain_hash != expected_chain:
                print("FAIL: genesis chain_hash mismatch")
                print("EXPECTED:", expected_chain)
                print("GOT:", chain_hash)
                ok = False
                break
        else:
            prev_chain = rows[i - 1][6]
            expected_chain = sha256_hex((prev_chain + event_id + prev_event_id).encode("utf-8"))
            if chain_hash != expected_chain:
                print("FAIL: chain_hash mismatch at index", i)
                print("EXPECTED:", expected_chain)
                print("GOT:", chain_hash)
                ok = False
                break

        try:
            json.loads(payload_json)
        except Exception:
            print("FAIL: payload_json invalid at index", i)
            ok = False
            break

    if ok:
        print("OK: governance chain verified")
        print("ROWS:", len(rows))
        print("TIP_EVENT_ID:", rows[-1][0])
        print("TIP_CHAIN_HASH:", rows[-1][6])

if __name__ == "__main__":
    main()