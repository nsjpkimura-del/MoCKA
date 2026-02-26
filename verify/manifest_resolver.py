from __future__ import annotations

import json
import os
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List, Tuple

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization


ROOT = Path(__file__).resolve().parents[1]
FREEZE_MANIFEST_PATH = ROOT / "freeze_manifest.json"
SUMMARY_PATH = ROOT / "acceptance" / "summary_matrix.json"
REGISTRY_PATH = ROOT / "keys" / "public_keys.json"


# -------------------------
# JSON utilities
# -------------------------

def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def write_json(path: Path, obj: Any) -> None:
    atomic_write_text(path, json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


# -------------------------
# Canonical + hash
# -------------------------

def canonical_json_bytes(obj: Any) -> bytes:
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return s.encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return sha256(data).hexdigest()


# -------------------------
# Registry v2 strict-only
# -------------------------

def load_registry_v2() -> Dict[str, Any]:
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(f"registry not found: {REGISTRY_PATH}")

    reg = load_json(REGISTRY_PATH)
    if not isinstance(reg, dict):
        raise ValueError("registry must be object")

    if reg.get("schema") != "mocka.keys.ed25519.registry.v2":
        raise ValueError("registry schema must be v2")

    if not isinstance(reg.get("keys"), dict):
        raise ValueError("registry.keys must be object")

    policy = reg.get("policy", {})
    if not isinstance(policy, dict):
        raise ValueError("registry.policy must be object")

    # Default strict: require active keys unless explicitly false.
    require_active = policy.get("require_active_keys", True)
    if require_active is not True:
        raise ValueError("policy.require_active_keys must be true in strict-only mode")

    return reg


def resolve_public_key_strict(key_id: str) -> Ed25519PublicKey:
    reg = load_registry_v2()
    keys = reg["keys"]

    if key_id not in keys:
        raise ValueError(f"unknown key_id: {key_id}")

    entry = keys[key_id]
    if not isinstance(entry, dict):
        raise ValueError(f"invalid key entry: {key_id}")

    if entry.get("algorithm", "ed25519") != "ed25519":
        raise ValueError(f"unsupported algorithm: {key_id}")

    status = entry.get("status", "active")
    revoked_at = entry.get("revoked_at_utc", None)

    if status != "active":
        raise ValueError(f"key not active: {key_id}")

    if revoked_at is not None:
        raise ValueError(f"key revoked: {key_id}")

    rel = entry.get("public_pem_path", "")
    if not isinstance(rel, str) or not rel:
        raise ValueError(f"public_pem_path missing: {key_id}")

    pub_path = ROOT / rel
    if not pub_path.exists():
        raise FileNotFoundError(f"public key file missing: {pub_path}")

    pem = pub_path.read_bytes()
    pk = serialization.load_pem_public_key(pem)

    if not isinstance(pk, Ed25519PublicKey):
        raise TypeError("loaded key is not ed25519")

    return pk


# -------------------------
# Wrapper verification (strict)
# -------------------------

def verify_payload_hash(wrapper: Dict[str, Any]) -> None:
    payload = wrapper.get("payload", None)
    expected = wrapper.get("payload_hash", "")

    if payload is None:
        raise ValueError("wrapper.payload missing")

    if not isinstance(expected, str) or len(expected) != 64:
        raise ValueError("wrapper.payload_hash invalid")

    actual = sha256_hex(canonical_json_bytes(payload))
    if actual != expected:
        raise ValueError(f"payload_hash mismatch expected={expected} actual={actual}")


def verify_rows_ed25519(wrapper: Dict[str, Any]) -> None:
    rows = wrapper.get("rows", None)
    if not isinstance(rows, list):
        raise ValueError("wrapper.rows must be list")

    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"row[{idx}] must be object")

        if row.get("row_sig_alg", "") != "ed25519":
            raise ValueError(f"row[{idx}] invalid row_sig_alg")

        key_id = row.get("key_id", "")
        sig_hex = row.get("row_sig", "")

        if not isinstance(key_id, str) or len(key_id) != 64:
            raise ValueError(f"row[{idx}] invalid key_id")

        if not isinstance(sig_hex, str) or len(sig_hex) == 0:
            raise ValueError(f"row[{idx}] invalid row_sig")

        try:
            sig = bytes.fromhex(sig_hex)
        except Exception:
            raise ValueError(f"row[{idx}] row_sig hex decode failed")

        pk = resolve_public_key_strict(key_id)

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
        raise ValueError("unsupported wrapper schema")

    verify_payload_hash(wrapper)
    verify_rows_ed25519(wrapper)


# -------------------------
# Summary rebuild (legacy API kept)
# -------------------------

def _pack_key(idx: int, pack: Dict[str, Any]) -> Tuple[int, str, str]:
    # Deterministic ordering: authoritative first, then index, then sha256/path.
    authoritative = 0 if pack.get("authoritative") is True else 1
    sha = str(pack.get("sha256", ""))
    path = str(pack.get("path", ""))
    return (authoritative, idx, sha + "|" + path)


def rebuild_summary_matrix(strict_manifest: bool = True) -> Dict[str, Any]:
    if not FREEZE_MANIFEST_PATH.exists():
        raise FileNotFoundError(f"freeze_manifest not found: {FREEZE_MANIFEST_PATH}")

    manifest = load_json(FREEZE_MANIFEST_PATH)
    if not isinstance(manifest, dict):
        raise ValueError("freeze_manifest must be object")

    packs = manifest.get("verify_packs", [])
    if not isinstance(packs, list):
        raise ValueError("freeze_manifest.verify_packs must be list")

    errors: List[str] = []
    row_index: Dict[str, List[Dict[str, Any]]] = {}

    # Deterministic pack iteration
    pack_items: List[Tuple[int, Dict[str, Any]]] = []
    for i, p in enumerate(packs):
        if isinstance(p, dict):
            pack_items.append((i, p))
    pack_items.sort(key=lambda t: _pack_key(t[0], t[1]))

    for idx, pack in pack_items:
        rel_path = pack.get("path", "")
        if not isinstance(rel_path, str) or not rel_path:
            errors.append(f"PACK_PATH_INVALID idx={idx}")
            continue

        pack_file = ROOT / rel_path
        if not pack_file.exists():
            errors.append(f"PACK_NOT_FOUND path={rel_path}")
            continue

        try:
            wrapper = load_json(pack_file)
        except Exception as e:
            errors.append(f"PACK_LOAD_FAIL path={rel_path} err={type(e).__name__}:{e}")
            continue

        if not isinstance(wrapper, dict):
            errors.append(f"WRAPPER_INVALID path={rel_path}")
            continue

        try:
            verify_wrapper(wrapper)
        except Exception as e:
            errors.append(f"VERIFY_FAIL path={rel_path} err={type(e).__name__}:{e}")
            continue

        rows = wrapper.get("rows", [])
        if not isinstance(rows, list):
            errors.append(f"ROWS_INVALID path={rel_path}")
            continue

        for r in rows:
            if not isinstance(r, dict):
                errors.append(f"ROW_INVALID path={rel_path}")
                continue

            row_id = r.get("row_id", "")
            if not isinstance(row_id, str) or not row_id:
                errors.append(f"ROW_ID_MISSING path={rel_path}")
                continue

            row_index.setdefault(row_id, []).append(r)

    # Deterministic row selection per row_id: canonical hash tie-break
    resolved_rows: Dict[str, Any] = {}
    for row_id in sorted(row_index.keys()):
        candidates = row_index[row_id]
        candidates.sort(key=lambda rr: sha256_hex(canonical_json_bytes(rr)))
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
    print(f"SUMMARY_HASH: {summary_hash}")

    if strict_manifest and errors:
        raise RuntimeError("STRICT_MANIFEST_FAIL: " + " | ".join(errors))

    return summary


# -------------------------
# CLI
# -------------------------

def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--wrapper", default="", help="verify single wrapper")
    ap.add_argument("--rebuild-summary", action="store_true", help="rebuild summary from freeze_manifest")
    args = ap.parse_args()

    # Legacy default: no args => rebuild summary strict
    if args.rebuild_summary or (not args.wrapper):
        rebuild_summary_matrix(strict_manifest=True)
        return 0

    wpath = Path(args.wrapper)
    wrapper = load_json(wpath)
    if not isinstance(wrapper, dict):
        raise ValueError("wrapper must be object")

    verify_wrapper(wrapper)

    print("STRICT_OK")
    print(f"wrapper={wpath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())