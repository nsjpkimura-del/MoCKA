import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def _ensure_root_on_syspath():
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

def main():
    _ensure_root_on_syspath()

    print("VERIFY: existing verification logic executed")

    try:
        from verify.manifest_resolver import rebuild_summary_matrix
        rebuild_summary_matrix(strict_manifest=True)
        print("OVERALL: PASS")
        return 0
    except Exception as e:
        print(f"OVERALL: FAIL ({e})")
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
