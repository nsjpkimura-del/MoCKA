import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def load_json(p: Path):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(p: Path, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def resolve_pack_priority(manifest: dict):
    packs = manifest.get("verify_packs", [])
    resolved = []
    for idx, p in enumerate(packs):
        priority = idx
        if p.get("authoritative") is True:
            priority = -1
        resolved.append(
            {
                "priority": int(priority),
                "sha256": str(p.get("sha256", "")),
                "authoritative": bool(p.get("authoritative", False)),
                "pack": p,
            }
        )
    resolved.sort(key=lambda x: (x["priority"], x["sha256"]))
    return resolved

def rebuild_summary_matrix():
    manifest_path = ROOT / "freeze_manifest.json"
    summary_path = ROOT / "acceptance" / "summary_matrix.json"

    manifest = load_json(manifest_path)
    resolved = resolve_pack_priority(manifest)

    summary = {
        "phase": manifest.get("phase"),
        "pack_count": len(resolved),
        "packs": [
            {
                "priority": r["priority"],
                "sha256": r["sha256"],
                "authoritative": r["authoritative"],
            }
            for r in resolved
        ],
    }

    write_json(summary_path, summary)
    print("OK: rebuilt summary_matrix")
    print(f"UPDATED: {summary_path}")

if __name__ == "__main__":
    rebuild_summary_matrix()
