import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def load_json(p: Path):
    # BOMが付いていても落ちないように utf-8-sig で読む
    with open(p, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def write_json(p: Path, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    # 書き出しはBOM無しで統一
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def sha256_bytes(b: bytes):
    return hashlib.sha256(b).hexdigest()

def canonical_json_bytes(obj):
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

def rebuild_summary_matrix(strict_manifest=True):
    manifest_path = ROOT / "freeze_manifest.json"
    summary_path = ROOT / "acceptance" / "summary_matrix.json"

    manifest = load_json(manifest_path)
    packs = resolve_pack_priority(manifest)

    errors = []
    row_index = {}

    for pack in packs:
        pack_file = ROOT / pack["path"]

        if not pack_file.exists():
            errors.append(f"NOT_FOUND: {pack_file}")
            continue

        if not pack_file.is_file():
            errors.append(f"NOT_A_FILE: {pack_file}")
            continue

        pack_json = load_json(pack_file)
        rows = pack_json.get("rows", [])

        for row in rows:
            row_id = row.get("row_id")
            if not row_id:
                continue

            candidate = {
                "pack_priority": pack["priority"],
                "pack_sha256": pack["sha256"],
                "row_sha256": sha256_bytes(canonical_json_bytes(row)),
                "row": row,
            }

            row_index.setdefault(row_id, []).append(candidate)

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

    summary_hash = sha256_bytes(canonical_json_bytes(summary))
    summary["summary_hash"] = summary_hash

    write_json(summary_path, summary)

    print("OK: deterministic summary rebuilt")
    print(f"SUMMARY_HASH: {summary_hash}")

    if strict_manifest and errors:
        raise RuntimeError("STRICT_MANIFEST_FAIL: " + " | ".join(errors))

if __name__ == "__main__":
    rebuild_summary_matrix(strict_manifest=True)
