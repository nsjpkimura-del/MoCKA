import argparse
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple


TS_RE = re.compile(r"^\d{8}_\d{6}$")


def now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def phase11_root() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def backup_root() -> str:
    return os.path.join(phase11_root(), "backup")


def is_ts_dir(name: str) -> bool:
    return TS_RE.match(name) is not None


def list_ts_dirs(root: str) -> List[str]:
    if not os.path.isdir(root):
        return []
    dirs = []
    for name in os.listdir(root):
        p = os.path.join(root, name)
        if os.path.isdir(p) and is_ts_dir(name):
            dirs.append(name)
    # newest first
    dirs.sort(reverse=True)
    return dirs


def collect_entries(
    bkp_root: str,
    file_filter: Optional[str],
    top: int,
    include_hash: bool
) -> List[Dict]:
    ts_dirs = list_ts_dirs(bkp_root)
    out: List[Dict] = []

    for ts in ts_dirs:
        ts_path = os.path.join(bkp_root, ts)
        try:
            names = sorted(os.listdir(ts_path))
        except OSError:
            continue

        for fn in names:
            if file_filter and file_filter not in fn:
                continue

            fp = os.path.join(ts_path, fn)
            if not os.path.isfile(fp):
                continue

            size = os.path.getsize(fp)
            item = {
                "timestamp_dir": ts,
                "backup_dir": ts_path,
                "file_name": fn,
                "file_path": fp,
                "size_bytes": size,
            }

            if include_hash:
                # SHA256 without external deps
                import hashlib
                h = hashlib.sha256()
                with open(fp, "rb") as f:
                    for chunk in iter(lambda: f.read(1024 * 1024), b""):
                        h.update(chunk)
                item["sha256"] = h.hexdigest()

            out.append(item)

            if top > 0 and len(out) >= top:
                return out

    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase11 backup search (read-only)")
    ap.add_argument("--file", dest="file_filter", default="", help="substring filter for file_name")
    ap.add_argument("--top", dest="top", type=int, default=50, help="max results (newest-first)")
    ap.add_argument("--hash", dest="include_hash", action="store_true", help="include sha256 (slower)")
    ap.add_argument("--out", dest="out_path", default="", help="output json path (default: outbox)")
    args = ap.parse_args()

    bkp_root = backup_root()
    results = collect_entries(
        bkp_root=bkp_root,
        file_filter=args.file_filter.strip() or None,
        top=max(0, args.top),
        include_hash=bool(args.include_hash),
    )

    payload = {
        "event_type": "backup_search",
        "generated_at": now_ts(),
        "backup_root": bkp_root,
        "query": {
            "file_substring": args.file_filter.strip(),
            "top": args.top,
            "include_hash": bool(args.include_hash),
        },
        "result_count": len(results),
        "results": results,
    }

    if args.out_path.strip():
        outp = args.out_path.strip()
    else:
        outbox = os.path.join(os.path.dirname(os.path.dirname(phase11_root())), "outbox")
        # phase11_root = ...\infield\phase11
        # outbox is ...\outbox
        # safer: absolute path to C:\Users\sirok\MoCKA\outbox but derive dynamically:
        # C:\Users\sirok\MoCKA\infield\phase11 -> C:\Users\sirok\MoCKA\outbox
        mocka_root = os.path.dirname(os.path.dirname(phase11_root()))
        outbox = os.path.join(mocka_root, "outbox")
        os.makedirs(outbox, exist_ok=True)
        outp = os.path.join(outbox, f"backupsearch_{payload['generated_at']}.json")

    with open(outp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"OUTPUT_JSON: {outp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
