import json
import hashlib
import os
from pathlib import Path

from verify.row_sign import verify_row_soft

ROOT = Path(__file__).resolve().parent.parent


def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def write_json(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def sha256_hex_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical_json_bytes(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def resolve_pack_priority(manifest):
    packs = manifest.get("verify_packs", [])
    resolved = []

    for idx, p in enumerate(packs):
        priority = idx
        if p.get("authoritative") is True:
            priority = -1

        resolved.append({
            "priority": int(priority),
            "sha256": str(p.get("sha256", "")),
            "path": str(p.get("path", "")),
        })

    resolved.sort(key=lambda x: (x["priority"], x["sha256"]))
    return resolved


def verify_wrapper_payload(wrapper, errors, pack_path):
    payload = wrapper.get("payload")
    payload_hash = wrapper.get("payload_hash")

    if payload is None:
        errors.append(f"WRAPPER_NO_PAYLOAD: {pack_path}")
        return

    computed = sha256_hex_bytes(canonical_json_bytes(payload))
    if computed != payload_hash:
        errors.append(f"WRAPPER_PAYLOAD_HASH_MISMATCH: {pack_path}")


def verify_row_signature(row, secret, errors):
    row_id = row.get("row_id")
    if not row_id:
        errors.append("ROW_NO_ID")
        return

    if "row_sig" not in row:
        errors.append(f"ROW_NO_SIGNATURE: row_id={row_id}")
        return

    if not secret:
        errors.append(f"ROW_SIG_SECRET_MISSING: row_id={row_id}")
        return

    ok, _ = verify_row_soft(row, str(row.get("row_sig")), secret)
    if not ok:
        errors.append(f"ROW_SIG_FAIL: row_id={row_id}")


def rebuild_summary_matrix(strict_manifest=True):
    manifest_path = ROOT / "freeze_manifest.json"
    summary_path = ROOT / "acceptance" / "summary_matrix.json"

    manifest = load_json(manifest_path)
    packs = resolve_pack_priority(manifest)

    errors = []
    row_index = {}

    secret = os.environ.get("MOCKA_ROW_SIG_SECRET", "")

    for pack in packs:
        pack_file = ROOT / pack["path"]

        if not pack_file.exists():
            errors.append(f"NOT_FOUND: {pack_file}")
            continue

        wrapper = load_json(pack_file)

        verify_wrapper_payload(wrapper, errors, pack["path"])

        rows = wrapper.get("rows", [])
        if not isinstance(rows, list):
            errors.append(f"WRAPPER_ROWS_INVALID: {pack['path']}")
            continue

        for row in rows:
            verify_row_signature(row, secret, errors)

            candidate = {
                "pack_priority": pack["priority"],
                "pack_sha256": pack["sha256"],
                "row_sha256": sha256_hex_bytes(canonical_json_bytes(row)),
                "row": row,
            }

            row_index.setdefault(row["row_id"], []).append(candidate)

    resolved_rows = {}

    for row_id, candidates in row_index.items():
        candidates.sort(
            key=lambda c: (
                c["pack_priority"],
                c["pack_sha256"],
                c["row_sha256"],
            )
        )
        resolved_rows[row_id] = candidates[0]["row"]

    summary = {
        "phase": manifest.get("phase"),
        "row_count": len(resolved_rows),
        "rows": resolved_rows,
        "manifest_errors": errors,
    }

    summary_hash = sha256_hex_bytes(canonical_json_bytes(summary))
    summary["summary_hash"] = summary_hash

    write_json(summary_path, summary)

    print("OK: deterministic summary rebuilt")
    print(f"SUMMARY_HASH: {summary_hash}")

    if strict_manifest and errors:
        raise RuntimeError("STRICT_MANIFEST_FAIL: " + " | ".join(errors))


if __name__ == "__main__":
    rebuild_summary_matrix(strict_manifest=True)