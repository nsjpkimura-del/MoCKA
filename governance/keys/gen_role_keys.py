from __future__ import annotations
import base64
import json
import os
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

def write_keypair(name: str) -> dict:
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

    priv_path = KEYDIR / f"{name}.ed25519.private.pem"
    pub_path = KEYDIR / f"{name}.ed25519.public.b64u"

    priv_path.write_bytes(priv_pem)
    pub_path.write_text(b64u(pub_raw), encoding="utf-8")

    return {
        "key_id": f"{name}_v1",
        "key_version": 1,
        "public_key_b64u": b64u(pub_raw),
        "activated_at_utc": utc_now(),
        "revoked_at_utc": None
    }

def main():
    KEYDIR.mkdir(parents=True, exist_ok=True)

    if not REG.exists():
        raise SystemExit(f"registry not found: {REG}")

    reg = json.loads(REG.read_text(encoding="utf-8-sig"))

    root_entry = write_keypair("root_key")
    op_entry = write_keypair("operational_key")

    reg.setdefault("root_keys", [])
    reg.setdefault("operational_keys", [])

    reg["root_keys"].append(root_entry)
    reg["operational_keys"].append(op_entry)

    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")
    print("OK: generated root_key + operational_key and registered public keys")
    print("NOTE: private keys stored under governance/keys/*.private.pem (protect them)")

if __name__ == "__main__":
    main()
