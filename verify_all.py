from __future__ import annotations
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def run_step(name: str, cmd: list[str]) -> None:
    print(f"[verify_all] STEP: {name}")
    r = subprocess.run(cmd)
    if r.returncode != 0:
        print(f"[verify_all] FAIL at {name}")
        sys.exit(r.returncode)
    print(f"[verify_all] OK: {name}")

def main() -> int:
    run_step("governance_event_required", [sys.executable, str(ROOT / "governance" / "verify_governance_event_required.py")])
    run_step("revoke_event", [sys.executable, str(ROOT / "governance" / "verify_revoke_event.py")])
    run_step("role_policy", [sys.executable, str(ROOT / "governance" / "verify_role_policy.py")])
    run_step("approval_flow", [sys.executable, str(ROOT / "governance" / "verify_approval_flow.py")])
    run_step("deterministic_build_gate", [sys.executable, str(ROOT / "governance" / "deterministic_build_gate.py")])
    run_step("chaos_gate", [sys.executable, str(ROOT / "governance" / "chaos_gate.py")])
    run_step("anchor_interface", [sys.executable, str(ROOT / "governance" / "verify_anchor_interface.py")])
    run_step("external_audit_report_interface", [sys.executable, str(ROOT / "governance" / "verify_external_audit_report.py")])

    if (ROOT / "verify.manifest_resolver.py").exists():
        run_step("manifest_resolver", [sys.executable, str(ROOT / "verify.manifest_resolver.py")])

    print("[verify_all] ALL CHECKS PASSED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
