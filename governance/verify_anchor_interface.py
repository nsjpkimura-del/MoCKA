from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8-sig"))

def main() -> int:
    ap = ROOT / "governance" / "anchor_record.json"
    if not ap.exists():
        print("FAIL: anchor_record.json not found (required)")
        return 2

    d = load_json(ap)
    if d.get("schema") != "mocka.governance.anchor_record.v1":
        print("FAIL: invalid anchor_record schema")
        return 3

    sealed = d.get("sealed_summary_hash")
    if not isinstance(sealed, str) or len(sealed) != 64:
        print("FAIL: sealed_summary_hash must be 64-hex string")
        return 4

    # calc_summary_hash の結果と一致することを強制
    import subprocess
    sh = subprocess.check_output([sys.executable, str(ROOT / "governance" / "calc_summary_hash.py")]).decode().strip()
    if sh != sealed:
        print("FAIL: anchor_record sealed_summary_hash mismatch")
        print("anchor:", sealed)
        print("calc  :", sh)
        return 5

    print("PASS: anchor_record present + summary_hash matches")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
