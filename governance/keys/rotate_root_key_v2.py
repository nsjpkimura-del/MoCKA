from __future__ import annotations
import base64, json
from pathlib import Path
from datetime import datetime, timezone
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

ROOT = Path(__file__).resolve().parents[2]
KEYDIR = ROOT / "governance" / "keys"
REG = ROOT / "governance" / "registry.json"

def b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")

def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def main() -> int:
    KEYDIR.mkdir(parents=True, exist_ok=True)
    reg = json.loads(REG.read_text(encoding="utf-8-sig"))

    priv = ed25519.Ed25519PrivateKey.generate()
    pub = priv.public_key()

    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_raw = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    priv_path = KEYDIR / "root_key_v2.ed25519.private.pem"
    pub_path  = KEYDIR / "root_key_v2.ed25519.public.b64u"
    priv_path.write_bytes(priv_pem)
    pub_path.write_text(b64u(pub_raw), encoding="utf-8")

    entry = {
        "key_id": "root_key_v2",
        "key_version": 2,
        "public_key_b64u": b64u(pub_raw),
        "activated_at_utc": utc_now(),
        "revoked_at_utc": None
    }

    reg.setdefault("root_keys", [])
    reg["root_keys"].append(entry)

    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")
    print("OK: root_key_v2 generated and registered")
    print("private:", priv_path)
    print("public :", pub_path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
