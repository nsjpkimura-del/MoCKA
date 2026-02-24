# C:\Users\sirok\MoCKA\audit\ed25519\governance\governance_ops.py
# note: Phase14.6 governance ops helpers (decision events before proof-side actions)

import sys
import os
import json
from governance_writer import append_event

ROOT = r"C:\Users\sirok\MoCKA"

def usage() -> int:
    print("USAGE:")
    print("  python governance_ops.py classify @payload.json \"note: ...\"")
    print("  python governance_ops.py quarantine @payload.json \"note: ...\"")
    print("  python governance_ops.py tip_reselect @payload.json \"note: ...\"")
    print("")
    print("PAYLOAD_JSON file recommended (PowerShell safe).")
    return 2

def read_payload_arg(arg: str) -> str:
    if arg == "-":
        return sys.stdin.read()
    if arg.startswith("@"):
        path = arg[1:]
        if not os.path.isabs(path):
            path = os.path.join(ROOT, path)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return arg

def require_note(note: str) -> None:
    if "note:" not in note:
        raise RuntimeError("REJECTED: note must include 'note:' prefix")

def cmd_classify(payload_arg: str, note: str) -> int:
    require_note(note)
    payload = json.loads(read_payload_arg(payload_arg))
    # expected keys example: {"target_event_id":"...","from":"historical_test","to":"quarantined","reason":"..."}
    eid = append_event("CLASSIFICATION_CHANGE_DECISION", payload, note)
    print("OK: appended CLASSIFICATION_CHANGE_DECISION")
    print("EVENT_ID:", eid)
    return 0

def cmd_quarantine(payload_arg: str, note: str) -> int:
    require_note(note)
    payload = json.loads(read_payload_arg(payload_arg))
    # expected keys example: {"target_event_id":"...","action":"quarantine|release","reason":"...","snapshot_path":"..."}
    eid = append_event("QUARANTINE_ACTION_DECISION", payload, note)
    print("OK: appended QUARANTINE_ACTION_DECISION")
    print("EVENT_ID:", eid)
    return 0

def cmd_tip_reselect(payload_arg: str, note: str) -> int:
    require_note(note)
    payload = json.loads(read_payload_arg(payload_arg))
    # expected keys example: {"proof_tip":"...","method":"phase14_reselect_tip","reason":"..."}
    eid = append_event("TIP_RESELECT_DECISION", payload, note)
    print("OK: appended TIP_RESELECT_DECISION")
    print("EVENT_ID:", eid)
    return 0

def main(argv) -> int:
    if len(argv) < 4:
        return usage()
    cmd = argv[1]
    payload_arg = argv[2]
    note = argv[3]

    try:
        if cmd == "classify":
            return cmd_classify(payload_arg, note)
        if cmd == "quarantine":
            return cmd_quarantine(payload_arg, note)
        if cmd == "tip_reselect":
            return cmd_tip_reselect(payload_arg, note)
    except Exception as e:
        print("ERROR:", str(e))
        return 2

    return usage()

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))