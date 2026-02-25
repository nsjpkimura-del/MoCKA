import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUMMARY = ROOT / "acceptance" / "summary_matrix.json"

def run_once():
    p = subprocess.run([sys.executable, str(ROOT / "verify" / "verify_all.py")], capture_output=True, text=True)
    sys.stdout.write(p.stdout)
    sys.stderr.write(p.stderr)
    if p.returncode != 0:
        return None
    if not SUMMARY.exists():
        return None
    data = json.loads(SUMMARY.read_text(encoding="utf-8"))
    return data.get("summary_hash")

def main():
    h1 = run_once()
    if not h1:
        print("FAIL: first run did not produce summary_hash")
        return 2

    h2 = run_once()
    if not h2:
        print("FAIL: second run did not produce summary_hash")
        return 2

    if h1 != h2:
        print(f"FAIL: hash changed {h1} -> {h2}")
        return 2

    print(f"OK: deterministic hash ثابت {h1}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
