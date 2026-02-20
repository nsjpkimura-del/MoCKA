import argparse
import glob
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


def now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def phase11_root() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def mocka_root() -> str:
    # ...\MoCKA\infield\phase11 -> ...\MoCKA
    return os.path.dirname(os.path.dirname(phase11_root()))


def outbox_dir() -> str:
    return os.path.join(mocka_root(), "outbox")


def safe_read_json(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def pick_target_string(obj: Dict[str, Any]) -> str:
    # normalize fields across edit/restore logs
    t = obj.get("target", {})
    if isinstance(t, dict):
        p = t.get("path", "") or ""
        fn = t.get("file_name", "") or ""
        return (p + " " + fn).strip()
    return ""


def pick_note(obj: Dict[str, Any]) -> str:
    n = obj.get("note", "")
    return n if isinstance(n, str) else ""


def pick_event_type(obj: Dict[str, Any]) -> str:
    et = obj.get("event_type", "")
    return et if isinstance(et, str) else ""


def sort_key_time(obj: Dict[str, Any]) -> str:
    # prefer the timestamp field if present; else fallback to empty
    ts = obj.get("timestamp", "")
    return ts if isinstance(ts, str) else ""


def collect_logs(outbox: str, mode: str) -> List[str]:
    paths: List[str] = []
    if mode in ("edit", "all"):
        paths.extend(glob.glob(os.path.join(outbox, "file_edit_*.json")))
    if mode in ("restore", "all"):
        paths.extend(glob.glob(os.path.join(outbox, "file_restore_*.json")))
    # newest first by filename timestamp (lexicographic works)
    paths.sort(reverse=True)
    return paths


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase11 audit log search (read-only)")
    ap.add_argument("--type", dest="mode", default="all", choices=["all", "edit", "restore"])
    ap.add_argument("--file", dest="file_filter", default="", help="substring filter against target path/name")
    ap.add_argument("--note", dest="note_filter", default="", help="substring filter against note (edit only)")
    ap.add_argument("--top", dest="top", type=int, default=50, help="max results (newest-first)")
    ap.add_argument("--out", dest="out_path", default="", help="output json path (default: outbox)")
    args = ap.parse_args()

    outbox = outbox_dir()
    os.makedirs(outbox, exist_ok=True)

    file_sub = args.file_filter.strip()
    note_sub = args.note_filter.strip()
    top = max(0, int(args.top))

    results: List[Dict[str, Any]] = []
    for p in collect_logs(outbox, args.mode):
        obj = safe_read_json(p)
        if not obj:
            continue

        et = pick_event_type(obj)
        tgt = pick_target_string(obj)
        note = pick_note(obj)

        if file_sub and file_sub not in tgt:
            continue

        if note_sub:
            # only meaningful for edit logs, but keep safe across types
            if note_sub not in note:
                continue

        results.append(
            {
                "log_path": p,
                "event_type": et,
                "timestamp": obj.get("timestamp", ""),
                "note": note,
                "target": obj.get("target", {}),
                "source": obj.get("source", obj.get("backup", {})),
            }
        )

        if top > 0 and len(results) >= top:
            break

    # stable sort by timestamp string descending if present
    results.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)

    payload = {
        "event_type": "audit_search",
        "generated_at": now_ts(),
        "outbox": outbox,
        "query": {
            "type": args.mode,
            "file_substring": file_sub,
            "note_substring": note_sub,
            "top": top,
        },
        "result_count": len(results),
        "results": results,
    }

    if args.out_path.strip():
        outp = args.out_path.strip()
    else:
        outp = os.path.join(outbox, f"auditsearch_{payload['generated_at']}.json")

    with open(outp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"OUTPUT_JSON: {outp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
