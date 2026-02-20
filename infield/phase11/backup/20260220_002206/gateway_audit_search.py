import os
import json
import glob
import argparse
from datetime import datetime

OUTBOX_DIR = r"C:\Users\sirok\MoCKA\outbox"


def collect_logs(mode: str):
    paths = []

    if mode in ("edit", "all"):
        paths.extend(glob.glob(os.path.join(OUTBOX_DIR, "file_edit_*.json")))

    if mode in ("restore", "all"):
        paths.extend(glob.glob(os.path.join(OUTBOX_DIR, "file_restore_*.json")))

    paths.sort(reverse=True)
    return paths


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def target_text(obj):
    t = obj.get("target", {})
    p = t.get("path", "") or ""
    fn = t.get("file_name", "") or ""
    return (p + " " + fn).lower()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", default="all")
    parser.add_argument("--file", default="")
    parser.add_argument("--note", default="")
    parser.add_argument("--top", type=int, default=20)

    args = parser.parse_args()

    mode = args.type.lower()
    file_sub = args.file.lower()
    note_sub = args.note.lower()
    top = args.top

    paths = collect_logs(mode)

    results = []

    for p in paths:
        obj = load_json(p)
        if not obj:
            continue

        tgt = target_text(obj)
        note = (obj.get("note", "") or "").lower()

        if file_sub and file_sub not in tgt:
            continue

        if note_sub and note_sub not in note:
            continue

        results.append({
            "timestamp": obj.get("timestamp"),
            "event_type": obj.get("event_type"),
            "note": obj.get("note"),
            "target_file": obj.get("target", {}).get("file_name"),
            "log_file": os.path.basename(p)
        })

        if top > 0 and len(results) >= top:
            break

    out = {
        "event_type": "audit_search",
        "generated_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "outbox": OUTBOX_DIR,
        "query": {
            "type": mode,
            "file_substring": file_sub,
            "note_substring": note_sub,
            "top": top
        },
        "result_count": len(results),
        "results": results
    }

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(OUTBOX_DIR, f"auditsearch_{ts}.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"OUTPUT_JSON: {out_path}")


if __name__ == "__main__":
    main()
