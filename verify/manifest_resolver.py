from __future__ import annotations

import json
import os
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization


ROOT = Path(__file__).resolve().parents[1]
FREEZE_MANIFEST_PATH = ROOT / "freeze_manifest.json"
SUMMARY_PATH = ROOT / "acceptance" / "summary_matrix.json"
REGISTRY_PATH = ROOT / "keys" / "public_keys.json"


# -------------------------------------------------
# JSON helpers
# -------------------------------------------------

def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


# -------------------------------------------------
# Canonical + Hash
# -------------------------------------------------

def canonical_json_bytes(obj: Any) -> bytes:
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return s.encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return sha256(data).hexdigest()


# -------------------------------------------------
# Registry (v1 / v2 compatible)
# -------------------------------------------------

def load_registry() -> Dict[str, Any]:
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError("registry not found")

    reg = load_json(REGISTRY_PATH)

    if not isinstance(reg, dict):
        raise ValueError("invalid registry")

    schema = reg.get("schema", "")

    if schema not in (
        "mocka.keys.ed25519.registry.v1",
        "mocka.keys.ed25519.registry.v2",
    ):
        raise ValueError("unsupported registry schema")

    if "keys" not in reg or not isinstance(reg["keys"], dict):
        raise ValueError("invalid registry keys")

    return reg


def resolve_public_key(key_id: str) -> Ed25519PublicKey:
    reg = load_registry()
    keys = reg["keys"]

    if key_id not in keys:
        raise ValueError(f"unknown key_id: {key_id}")

    entry = keys[key_id]

    status = entry.get("status", "active")
    revoked_at = entry.get("revoked_at_utc")

    policy = reg.get("policy", {})
    require_active = policy.get("require_active_keys", False)

    if require_active:
        if status != "active":
            raise ValueError(f"key not active: {key_id}")
        if revoked_at is not None:
            raise ValueError(f"key revoked: {key_id}")

    rel_path = entry.get("public_pem_path")
    if not isinstance(rel_path, str) or not rel_path:
        raise ValueError("invalid public_pem_path")

    pub_path = ROOT / rel_path
    if not pub_path.exists():
        raise FileNotFoundError(f"public key file missing: {pub_path}")

    pem = pub_path.read_bytes()
    pk = serialization.load_pem_public_key(pem)

    if not isinstance(pk, Ed25519PublicKey):
        raise TypeError("loaded key is not Ed25519")

    return pk


# -------------------------------------------------
# STRICT wrapper verification
# -------------------------------------------------

def verify_payload_hash(wrapper: Dict[str, Any]) -> None:
    payload = wrapper.get("payload")
    expected = wrapper.get("payload_hash")

    if not isinstance(payload, dict):
        raise ValueError("invalid payload")

    actual = sha256_hex(canonical_json_bytes(payload))

    if actual != expected:
        raise ValueError("payload_hash mismatch")


def verify_rows(wrapper: Dict[str, Any]) -> None:
    rows = wrapper.get("rows")
    if not isinstance(rows, list):
        raise ValueError("wrapper.rows invalid")

    for idx, row in enumerate(rows):
        if row.get("row_sig_alg") != "ed25519":
            raise ValueError(f"row[{idx}] invalid row_sig_alg")

        key_id = row.get("key_id")
        sig_hex = row.get("row_sig")

        if not isinstance(key_id, str) or len(key_id) != 64:
            raise ValueError("invalid key_id")

        if not isinstance(sig_hex, str):
            raise ValueError("invalid row_sig")

        try:
            sig = bytes.fromhex(sig_hex)
        except Exception:
            raise ValueError("row_sig hex decode failed")

        pk = resolve_public_key(key_id)

        row_copy = dict(row)
        row_copy.pop("row_sig", None)
        row_copy.pop("row_sig_alg", None)
        row_copy.pop("key_id", None)

        msg = canonical_json_bytes(row_copy)

        try:
            pk.verify(sig, msg)
        except Exception:
            raise ValueError("signature verification failed")


def verify_wrapper(wrapper: Dict[str, Any]) -> None:
    if wrapper.get("schema") != "mocka.pack.wrapper.signed.v2":
        raise ValueError("unsupported wrapper schema")

    verify_payload_hash(wrapper)
    verify_rows(wrapper)


# -------------------------------------------------
# Summary rebuild
# -------------------------------------------------

def rebuild_summary_matrix(strict_manifest: bool = True) -> Dict[str, Any]:
    manifest = load_json(FREEZE_MANIFEST_PATH)

    packs = manifest.get("verify_packs", [])

    errors: List[str] = []
    row_index: Dict[str, List[Dict[str, Any]]] = {}

    for idx, pack in enumerate(packs):
        path = pack.get("path")
        if not isinstance(path, str):
            continue

        file_path = ROOT / path
        if not file_path.exists():
            errors.append(f"NOT_FOUND: {path}")
            continue

        wrapper = load_json(file_path)

        try:
            verify_wrapper(wrapper)
        except Exception as e:
            errors.append(f"VERIFY_FAIL: {path} | {e}")
            continue

        rows = wrapper.get("rows", [])
        for row in rows:
            row_id = row.get("row_id")
            if not row_id:
                continue

            row_index.setdefault(row_id, []).append(row)

    resolved_rows: Dict[str, Any] = {}
    for row_id, candidates in row_index.items():
        resolved_rows[row_id] = candidates[0]

    summary: Dict[str, Any] = {
        "phase": manifest.get("phase"),
        "row_count": len(resolved_rows),
        "rows": resolved_rows,
        "manifest_errors": errors,
    }

    summary_hash = sha256_hex(canonical_json_bytes(summary))
    summary["summary_hash"] = summary_hash

    write_json(SUMMARY_PATH, summary)

    print("OK: deterministic summary rebuilt")
    print("SUMMARY_HASH:", summary_hash)

    if strict_manifest and errors:
        raise RuntimeError("STRICT_MANIFEST_FAIL: " + " | ".join(errors))

    return summary


# -------------------------------------------------
# CLI
# -------------------------------------------------

def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--wrapper", default="")
    ap.add_argument("--rebuild-summary", action="store_true")
    args = ap.parse_args()

    if args.rebuild_summary or (not args.wrapper):
        rebuild_summary_matrix(strict_manifest=True)
        return 0

    wrapper = load_json(Path(args.wrapper))
    verify_wrapper(wrapper)

    print("STRICT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())