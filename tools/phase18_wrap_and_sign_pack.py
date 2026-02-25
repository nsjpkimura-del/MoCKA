import json
import sys
import os
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from verify.row_sign import sign_row_soft


def canonical_json_bytes(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_hex_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def write_json(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def relpath_str(p: Path) -> str:
    try:
        rp = p.resolve().relative_to(ROOT.resolve())
        return rp.as_posix()
    except Exception:
        return str(p)


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: python tools/phase18_wrap_and_sign_pack.py <input_pack.json> <output_wrapper.json>")
        return 2

    secret = os.environ.get("MOCKA_ROW_SIG_SECRET")
    if not secret:
        print("ERROR: set MOCKA_ROW_SIG_SECRET env first")
        return 2

    inp = Path(sys.argv[1])
    out = Path(sys.argv[2])

    if not inp.exists():
        print(f"ERROR: input not found: {inp}")
        return 2

    payload = load_json(inp)
    payload_hash = sha256_hex_bytes(canonical_json_bytes(payload))
    pack_sha256 = sha256_hex_bytes(inp.read_bytes())

    row = {
        "row_id": f"pack:{pack_sha256}",
        "pack_sha256": pack_sha256,
        "payload_hash": payload_hash,
        "source_path": relpath_str(inp),
    }

    row["row_sig"] = sign_row_soft(row, secret)

    wrapper = {
        "schema": "mocka.pack.wrapper.signed.v2",
        "pack_sha256": pack_sha256,
        "payload_hash": payload_hash,
        "payload": payload,
        "rows": [row],
    }

    write_json(out, wrapper)

    print("SIGNED_ROWS: 1")
    print(f"ROW_ID: {row['row_id']}")
    print(f"WROTE: {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())