# ingest_outbox.py
# ASCII only. UTF-8 BOM accepted on input.

from __future__ import annotations

import argparse
import glob
import json
import os
import sqlite3
import sys
from typing import Any, Dict, List, Optional, Tuple

DDL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS file_edit (
  id TEXT PRIMARY KEY,
  ts_local TEXT NOT NULL,
  outbox_file TEXT NOT NULL UNIQUE,
  target_path TEXT NOT NULL,
  backup_path TEXT NOT NULL,
  sha256_source TEXT NOT NULL,
  sha256_after TEXT NOT NULL,
  json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS file_restore (
  id TEXT PRIMARY KEY,
  ts_local TEXT NOT NULL,
  outbox_file TEXT NOT NULL UNIQUE,
  source_edit_outbox TEXT NOT NULL,
  target_path TEXT NOT NULL,
  backup_path TEXT NOT NULL,
  sha256_source_expected TEXT NOT NULL,
  sha256_after TEXT NOT NULL,
  restore_verified INTEGER NOT NULL,
  json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_event (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts_local TEXT NOT NULL,
  kind TEXT NOT NULL,
  outbox_file TEXT NOT NULL,
  message TEXT NOT NULL
);
"""

def read_json_utf8sig(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def ensure_parent_dir(path: str) -> None:
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)

def connect_db(db_path: str) -> sqlite3.Connection:
    ensure_parent_dir(db_path)
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys=ON;")
    con.executescript(DDL)
    return con

def s(x: Any) -> str:
    if x is None:
        return ""
    return str(x).strip()

def log_audit(con: sqlite3.Connection, ts_local: str, kind: str, outbox_file: str, message: str) -> None:
    con.execute(
        "INSERT INTO audit_event (ts_local,kind,outbox_file,message) VALUES (?,?,?,?)",
        (ts_local or "unknown", kind, os.path.abspath(outbox_file), message),
    )

def infer_kind(outbox_file: str, payload: Dict[str, Any]) -> str:
    # Newer style
    schema = s(payload.get("schema"))
    if schema.endswith("file_edit.v1"):
        return "edit"
    if schema.endswith("file_restore.v1"):
        return "restore"

    # Legacy style (your current outbox)
    et = s(payload.get("event_type")).lower()
    if et in ("file_edit", "edit"):
        return "edit"
    if et in ("file_restore", "restore"):
        return "restore"

    # Key signature
    if "restore_verified" in payload or "sha256_source_expected" in payload:
        return "restore"
    if "target_file" in payload or "search" in payload:
        return "edit"

    base = os.path.basename(outbox_file).lower()
    if base.startswith("file_restore_"):
        return "restore"
    if base.startswith("file_edit_"):
        return "edit"
    return ""

def ingest_one(con: sqlite3.Connection, outbox_file: str, payload: Dict[str, Any]) -> Tuple[str, str]:
    kind = infer_kind(outbox_file, payload)
    outbox_abs = os.path.abspath(outbox_file)
    ts = s(payload.get("ts_local")) or s(payload.get("timestamp")) or "unknown"
    js = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))

    if kind == "edit":
        # Accept both new and legacy keys
        _id = s(payload.get("id")) or s(payload.get("event_id")) or os.path.basename(outbox_abs)
        target_path = s(payload.get("target_path")) or s(payload.get("target")) or s(payload.get("target_file"))
        backup_path = s(payload.get("backup_path")) or s(payload.get("backup"))
        sha_src = s(payload.get("sha256_source")) or s(payload.get("hash_before")) or s(payload.get("hash_source"))
        sha_after = s(payload.get("sha256_after")) or s(payload.get("hash")) or s(payload.get("hash_after"))

        if not s(payload.get("schema")):
            log_audit(con, ts, "warn", outbox_abs, "missing schema; inferred edit/legacy")

        con.execute(
            "INSERT OR IGNORE INTO file_edit "
            "(id,ts_local,outbox_file,target_path,backup_path,sha256_source,sha256_after,json) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (_id, ts, outbox_abs, target_path, backup_path, sha_src, sha_after, js),
        )
        return ("file_edit", _id)

    if kind == "restore":
        _id = s(payload.get("id")) or s(payload.get("event_id")) or os.path.basename(outbox_abs)
        src_edit = s(payload.get("source_edit_outbox")) or s(payload.get("source_edit")) or ""
        target_path = s(payload.get("target_path")) or s(payload.get("target")) or s(payload.get("target_file"))
        backup_path = s(payload.get("backup_path")) or s(payload.get("backup"))
        sha_exp = s(payload.get("sha256_source_expected")) or s(payload.get("hash_before")) or s(payload.get("hash_source"))
        sha_after = s(payload.get("sha256_after")) or s(payload.get("hash")) or s(payload.get("hash_after"))
        rv = 1 if bool(payload.get("restore_verified", False)) else 0

        if not s(payload.get("schema")):
            log_audit(con, ts, "warn", outbox_abs, "missing schema; inferred restore/legacy")

        con.execute(
            "INSERT OR IGNORE INTO file_restore "
            "(id,ts_local,outbox_file,source_edit_outbox,target_path,backup_path,sha256_source_expected,sha256_after,restore_verified,json) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (_id, ts, outbox_abs, src_edit, target_path, backup_path, sha_exp, sha_after, rv, js),
        )
        return ("file_restore", _id)

    raise ValueError(f"Unknown schema/event_type: schema={s(payload.get('schema'))} event_type={s(payload.get('event_type'))}")

def iter_outbox_files(outbox_dir: str, only_file: Optional[str]) -> List[str]:
    if only_file:
        return [os.path.abspath(only_file)]
    files = glob.glob(os.path.join(outbox_dir, "file_edit_*.json")) + glob.glob(os.path.join(outbox_dir, "file_restore_*.json"))
    files = [os.path.abspath(p) for p in files]
    files.sort()
    return files

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--outbox", required=True)
    ap.add_argument("--file", default=None)
    args = ap.parse_args(argv)

    outbox = os.path.abspath(args.outbox)
    db = os.path.abspath(args.db)

    if not os.path.isdir(outbox):
        print(f"[ingest] outbox not found: {outbox}", file=sys.stderr)
        return 2

    files = iter_outbox_files(outbox, args.file)
    if not files:
        print("[ingest] nothing to ingest")
        return 0

    con = connect_db(db)
    try:
        ok = 0
        for f in files:
            try:
                payload = read_json_utf8sig(f)
                table, _id = ingest_one(con, f, payload)
                con.commit()
                ok += 1
                print(f"[ingest] ok table={table} file={f}")
            except Exception as e:
                con.rollback()
                print(f"[ingest] fail file={f} err={e}", file=sys.stderr)
                return 3
        print(f"[ingest] done total={len(files)} ok={ok} db={db}")
        return 0
    finally:
        con.close()

if __name__ == "__main__":
    raise SystemExit(main())