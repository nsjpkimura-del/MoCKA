from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    role_file = ROOT / "governance" / "keys" / "role_policy.json"
    if not role_file.exists():
        print("FAIL: role_policy.json not found")
        return 2

    data = json.loads(role_file.read_text(encoding="utf-8-sig"))

    if data.get("schema") != "mocka.keys.role.definition.v1":
        print("FAIL: invalid role policy schema")
        return 3

    if "root_key" not in data or "operational_key" not in data:
        print("FAIL: missing role definitions")
        return 4

    print("PASS: role policy interface valid")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
