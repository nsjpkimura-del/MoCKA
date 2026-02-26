# verify/manifest_resolver.py
# Phase20 Unified STRICT Resolver
# - wrapper v2 ONLY
# - payload_hash STRICT
# - Ed25519 row signature STRICT
# - public key registry required
# - deterministic canonical json

from __future__ import annotations

import json
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "keys" / "public_keys.json"


# ---------------------------------------------------------
# Canonical JSON
# ---------------------------------------------------------

def canonical_json_bytes(obj: Any) -> bytes:
    s = json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return s.encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return sha256(data).hexdigest()


# ---------------------------------------------------------
# Key Registry
# ---------------------------------------------------------

def load_registry() -> Dict[str, Any]:
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(f"registry not found: {REGISTRY_PATH}")
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def resolve_public_key(key_id: str) -> Ed25519PublicKey:
    registry = load_registry()

    keys = registry.get("keys", {})
    if key_id not in keys:
        raise ValueError(f"unknown key_id: {key_id}")

    rel_path = keys[key_id].get("public_pem_path", "")
    if not rel_path:
        raise ValueError(f"public_pem_path missing for key_id: {key_id}")

    pub_path = ROOT / rel_path
    if not pub_path.exists():
        raise FileNotFoundError(f"public key file missing: {pub_path}")

    pem = pub_path.read_bytes()
    pk = serialization.load_pem_public_key(pem)

    if not isinstance(pk, Ed25519PublicKey):
        raise TypeError("loaded key is not Ed25519")

    return pk


# ---------------------------------------------------------
# Verification Core
# ---------------------------------------------------------

def verify_payload_hash(wrapper: Dict[str, Any]) -> None:
    payload = wrapper.get("payload")
    if payload is None:
        raise ValueError("wrapper.payload missing")

    expected = wrapper.get("payload_hash", "")
    if not isinstance(expected, str) or len(expected) != 64:
        raise ValueError("invalid payload_hash")

    actual = sha256_hex(canonical_json_bytes(payload))

    if actual != expected:
        raise ValueError(
            f"payload_hash mismatch\nexpected={expected}\nactual  ={actual}"
        )


def verify_rows(wrapper: Dict[str, Any]) -> None:
    rows = wrapper.get("rows")
    if not isinstance(rows, list):
        raise ValueError("wrapper.rows must be list")

    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"row[{idx}] invalid")

        alg = row.get("row_sig_alg")
        if alg != "ed25519":
            raise ValueError(f"row[{idx}] invalid row_sig_alg")

        key_id = row.get("key_id")
        if not isinstance(key_id, str) or len(key_id) != 64:
            raise ValueError(f"row[{idx}] invalid key_id")

        sig_hex = row.get("row_sig")
        if not isinstance(sig_hex, str) or len(sig_hex) == 0:
            raise ValueError(f"row[{idx}] invalid row_sig")

        try:
            sig = bytes.fromhex(sig_hex)
        except Exception:
            raise ValueError(f"row[{idx}] row_sig hex decode failed")

        pk = resolve_public_key(key_id)

        # Remove signature fields before canonicalization
        row_for_verify = dict(row)
        row_for_verify.pop("row_sig", None)
        row_for_verify.pop("row_sig_alg", None)
        row_for_verify.pop("key_id", None)

        msg = canonical_json_bytes(row_for_verify)

        try:
            pk.verify(sig, msg)
        except Exception:
            raise ValueError(f"row[{idx}] signature verification failed")


def verify_wrapper(wrapper: Dict[str, Any]) -> None:
    if wrapper.get("schema") != "mocka.pack.wrapper.signed.v2":
        raise ValueError("unsupported schema")

    verify_payload_hash(wrapper)
    verify_rows(wrapper)


# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------

def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--wrapper", required=True)
    args = ap.parse_args()

    path = Path(args.wrapper)
    wrapper = json.loads(path.read_text(encoding="utf-8"))

    verify_wrapper(wrapper)

    print("STRICT_OK")
    print(f"wrapper={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())