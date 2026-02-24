# C:\Users\sirok\MoCKA\audit\ed25519\governance\governance_cli.py
# note: Phase14.6 Governance CLI (append/verify) robust payload input

import sys
import json
import subprocess
import os
from typing import Dict, Any
from governance_writer import append_event

ROOT = r"C:\Users\sirok\MoCKA"
VERIFY_PY = os.path.join(ROOT, "audit", "ed25519", "governance", "governance_chain_verify.py")

def usage() -> int:
    print("USAGE:")
    print("  python governance_cli.py verify")
    print("  python governance_cli.py append EVENT_TYPE PAYLOAD NOTE")
    print("")
    print("PAYLOAD forms:")
    print("  1) inline JSON string")
    print("  2) @path_to_json_file   (recommended on PowerShell)")
    print("  3) -                   (read JSON from stdin)")
    print("")
    print("EXAMPLE (file):")
    print("  python governance_cli.py append TIP_RESELECT_DECISION @payload.json \"note: ...\"")
    return 2

def cmd_verify() -> int:
    r = subprocess.run([sys.executable, VERIFY_PY], cwd=ROOT)
    return r.returncode

def read_payload_arg(payload_arg: str) -> str:
    if payload_arg == "-":
        return sys.stdin.read()

    if payload_arg.startswith("@"):
        path = payload_arg[1:]
        if not os.path.isabs(path):
            path = os.path.join(ROOT, path)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    return payload_arg

def cmd_append(argv) -> int:
    if len(argv) < 5:
        return usage()

    event_type = argv[2]
    payload_arg = argv[3]
    note = argv[4]

    if "note:" not in note:
        print("REJECTED: note must include 'note:' prefix")
        return 2

    payload_s = read_payload_arg(payload_arg)

    try:
        payload: Dict[str, Any] = json.loads(payload_s)
    except Exception as e:
        print("BAD_PAYLOAD_JSON")
        print("ERR:", str(e))
        print("PAYLOAD_RAW_REPR:", repr(payload_s))
        return 2

    eid = append_event(event_type, payload, note)
    print("OK: appended", event_type)
    print("EVENT_ID:", eid)
    return 0

def main(argv) -> int:
    if len(argv) < 2:
        return usage()
    if argv[1] == "verify":
        return cmd_verify()
    if argv[1] == "append":
        return cmd_append(argv)
    return usage()

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))