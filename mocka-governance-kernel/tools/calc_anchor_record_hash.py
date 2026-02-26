import argparse
import hashlib
import json
from pathlib import Path

def canonical_json_bytes(obj) -> bytes:
    # Deterministic canonical form: sorted keys, minimal separators, utf-8, no trailing newline.
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return s.encode("utf-8")

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--anchor", default="mocka-governance-kernel/anchors/anchor_record.json")
    ap.add_argument("--out", default="mocka-governance-kernel/anchors/anchor_record.sha256")
    args = ap.parse_args()

    anchor_path = Path(args.anchor)
    out_path = Path(args.out)

    if not anchor_path.exists():
        raise SystemExit(f"ERROR: anchor record not found: {anchor_path}")

    # NOTE: accept UTF-8 with BOM (utf-8-sig) for Windows PowerShell Set-Content compatibility.
    text = anchor_path.read_text(encoding="utf-8-sig")
    obj = json.loads(text)

    canon = canonical_json_bytes(obj)
    h = sha256_hex(canon)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(h + "\n", encoding="utf-8")
    print(f"OK: wrote {out_path} = {h}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
