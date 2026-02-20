# gateway_audit_search.py
# ASCII only.

from __future__ import annotations

import argparse
import glob
import json
import os
import sqlite3
import sys
from typing import Any, Dict, Iterable, List, Optional, Tuple

def read_json_utf8sig(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def search_payload(payload: Dict[str, Any], needle: str) -> bool:
    if not needle:
        return True
    s = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).lower()
    return needle.lower() in s

def outbox_iter(outbox_dir: str) -> Iterable[Tuple[str, Dict[str, Any]]]:
    pat1 = os.path.join(outbox_dir, "file_edit_*.json")
    pat2 = os.path.join(outbox_dir, "file_restore_*.json")
    files = glob.glob(pat1) + glob.glob(pat2)
    files = [os.path.abspath(p) for p in files]
    files.sort()
    for f in files:
        try:
            yield (f, read_json_utf8sig(f))
        except Exception:
            continue

def db_iter(db_path: str) -> Iterable[Tuple[str, Dict[str, Any]]]:
    con = sqlite3.connect(db_path)
    try:
        for table in ["file_edit", "file_restore"]:
            cur = con.execute(f"SELECT outbox_file, json FROM {table} ORDER BY ts_local ASC")
            for outbox_file, js in cur.fetchall():
                try:
                    yield (str(outbox_file), json.loads(js))
                except Exception:
                    continue
    finally:
        con.close()

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["outbox", "db"], required=True)
    ap.add_argument("--outbox", default=None)
    ap.add_argument("--db", default=None)
    ap.add_argument("--contains", default="", help="substring match (case-insensitive) against json")
    ap.add_argument("--schema", default="", help="exact schema match")
    ap.add_argument("--limit", type=int, default=200)
    args = ap.parse_args(argv)

    if args.source == "outbox":
        if not args.outbox:
            print("missing --outbox", file=sys.stderr)
            return 2
        it = outbox_iter(os.path.abspath(args.outbox))
    else:
        if not args.db:
            print("missing --db", file=sys.stderr)
            return 2
        it = db_iter(os.path.abspath(args.db))

    n = 0
    for src, payload in it:
        if args.schema and str(payload.get("schema", "")) != args.schema:
            continue
        if not search_payload(payload, args.contains):
            continue
        row = {"source": src, "payload": payload}
        sys.stdout.write(json.dumps(row, ensure_ascii=True) + "\n")
        n += 1
        if n >= args.limit:
            break

    return 0

if __name__ == "__main__":
    raise SystemExit(main())