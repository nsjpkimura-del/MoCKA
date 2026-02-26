from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    det_script = ROOT / "phase17_determinism_check.py"
    if not det_script.exists():
        print("INFO: phase17_determinism_check.py not present (determinism gate interface only)")
        return 0

    r = subprocess.run([sys.executable, str(det_script)])
    if r.returncode != 0:
        print("FAIL: determinism mismatch")
        return r.returncode

    print("PASS: determinism gate")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
