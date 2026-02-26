from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    report_file = ROOT / "governance" / "external_audit_report.json"
    if not report_file.exists():
        print("INFO: external_audit_report.json not present (optional interface)")
        return 0

    try:
        data = json.loads(report_file.read_text(encoding="utf-8"))
    except Exception as e:
        print("FAIL: invalid audit report json", e)
        return 2

    if data.get("schema") != "mocka.external.audit.report.v1":
        print("FAIL: invalid audit report schema")
        return 3

    if data.get("result") not in ("PASS", "FAIL"):
        print("FAIL: result must be PASS or FAIL")
        return 4

    if not isinstance(data.get("verification_steps"), list):
        print("FAIL: verification_steps must be list")
        return 5

    print("PASS: external audit report interface valid")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
