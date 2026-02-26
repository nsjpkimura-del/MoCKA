from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    p = ROOT / "governance" / "approval_flow.json"
    if not p.exists():
        print("FAIL: approval_flow.json not found")
        return 2
    d = json.loads(p.read_text(encoding="utf-8-sig"))
    if d.get("schema") != "mocka.governance.approval.flow.v1":
        print("FAIL: invalid approval flow schema")
        return 3
    flows = d.get("flows")
    if not isinstance(flows, dict):
        print("FAIL: flows must be dict")
        return 4
    if "multi_approver_flow" not in flows or "single_approver_flow" not in flows:
        print("FAIL: missing required flows")
        return 5
    print("PASS: approval flow interface valid")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
