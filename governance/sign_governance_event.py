from __future__ import annotations
import json
import base64
from pathlib import Path
from cryptography.hazmat.primitives import serialization

ROOT = Path(__file__).resolve().parents[1]
KEYDIR = ROOT / "governance" / "keys"
EVENT_PATH = ROOT / "governance" / "governance_event.json"

def b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")

def main() -> int:
    priv_path = KEYDIR / "root_key_v2.ed25519.private.pem"
    if not priv_path.exists():
        print("FAIL: root_key_v2 private not found")
        return 2

    private_key = serialization.load_pem_private_key(priv_path.read_bytes(), password=None)

    event = json.loads(EVENT_PATH.read_text(encoding="utf-8-sig"))
    event_copy = dict(event)
    event_copy["signature"] = ""

    msg = json.dumps(event_copy, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = private_key.sign(msg)

    event["signature"] = b64u(sig)
    EVENT_PATH.write_text(json.dumps(event, ensure_ascii=False, indent=2), encoding="utf-8")

    print("OK: governance_event signed with root_key_v2")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
