#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime, timezone

APPROVAL_FLAG = "governance/propagation/APPROVED_TO_SYNC.flag"
PUBLIC_JSON = "governance/propagation/public_index_v1.json"

def die(msg: str, code: int = 1) -> None:
    sys.stderr.write(msg.rstrip() + "\n")
    raise SystemExit(code)

def is_approved() -> bool:
    if not os.path.exists(APPROVAL_FLAG):
        return False
    try:
        with open(APPROVAL_FLAG, "r", encoding="utf-8-sig") as f:
            return f.read().strip() == "APPROVED"
    except Exception:
        return False

def audit_log(approved: bool, target: str, count: int) -> None:
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
    line = f"{ts} approved={str(approved).lower()} target={target} count={count}\n"
    os.makedirs("governance/propagation", exist_ok=True)
    with open("governance/propagation/sync_audit.log", "a", encoding="utf-8-sig", newline="\n") as f:
        f.write(line)

def main() -> None:
    approved = is_approved()
    with open(PUBLIC_JSON, "r", encoding="utf-8-sig") as f:
        payload = json.load(f)
    count = int(payload.get("count", 0))
    audit_log(approved, "sheets", count)

    if not approved:
        die("DENY: human approval flag missing or invalid")

    # Placeholder: actual Sheets API write will be implemented after credentials are set.
    die("HALT: Sheets sync not configured yet (no credentials)")

if __name__ == "__main__":
    main()



