import json
import hashlib
from pathlib import Path

# note: Phase23-A deterministic bundle_hash with BOM-safe read
BUNDLE_PATH = Path("governance") / "anchor_bundle.json"

def sha256_hex(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()

def main() -> int:
    if not BUNDLE_PATH.exists():
        raise FileNotFoundError(str(BUNDLE_PATH))

    # note: utf-8-sig strips UTF-8 BOM if present
    raw = BUNDLE_PATH.read_text(encoding="utf-8-sig")
    obj = json.loads(raw)

    # note: avoid self-reference
    obj["bundle_hash"] = ""

    canonical = json.dumps(
        obj,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    bh = sha256_hex(canonical)

    # note: write back normalized JSON without BOM
    obj["bundle_hash"] = bh
    BUNDLE_PATH.write_text(
        json.dumps(obj, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(bh)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
