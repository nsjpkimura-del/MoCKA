from __future__ import annotations
import json,base64
from pathlib import Path
from cryptography.hazmat.primitives import serialization

ROOT = Path(__file__).resolve().parents[1]
KEYDIR = ROOT / "governance" / "keys"
EV_PATH = ROOT / "governance" / "revoke_event.json"

def b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")

priv = serialization.load_pem_private_key(
    (KEYDIR / "root_key_v2.ed25519.private.pem").read_bytes(),
    password=None
)

ev = json.loads(EV_PATH.read_text(encoding="utf-8-sig"))
ev_copy = dict(ev)
ev_copy["signature"] = ""

msg = json.dumps(ev_copy, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
sig = priv.sign(msg)

ev["signature"] = b64u(sig)
EV_PATH.write_text(json.dumps(ev, ensure_ascii=False, indent=2), encoding="utf-8")
print("OK: revoke_event signed")
