import argparse
import json
import os
import sqlite3
import hashlib
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

DB_PATH = r"C:\Users\sirok\MoCKA\infield\phase11\knowledge.db"
OUTBOX_DIR = r"C:\Users\sirok\MoCKA\outbox"
PHASE11_DIR = r"C:\Users\sirok\MoCKA\infield\phase11"
SEARCH_FAST = r"C:\Users\sirok\MoCKA\infield\phase11\gateway_search_fast.py"

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def get_event_columns(conn: sqlite3.Connection) -> List[str]:
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(events)")
    rows = cur.fetchall()
    return [r[1] for r in rows]

def fetch_event_by_id(conn: sqlite3.Connection, event_id: str, columns: List[str]) -> Optional[Dict[str, Any]]:
    cur = conn.cursor()
    col_sql = ", ".join([f'"{c}"' for c in columns])
    cur.execute(f"SELECT {col_sql} FROM events WHERE id = ?", (event_id,))
    row = cur.fetchone()
    if row is None:
        return None
    item: Dict[str, Any] = {}
    for i, c in enumerate(columns):
        item[c] = row[i]
    return item

def integrity_recalc(event: Dict[str, Any]) -> str:
    if "content" in event and event["content"] is not None:
        return sha256_text(str(event["content"]))
    canonical = json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256_text(canonical)

def run_search_fast(query: str) -> Dict[str, Any]:
    if not os.path.isabs(SEARCH_FAST):
        raise RuntimeError("SEARCH_FAST must be absolute path")

    cmd = [sys.executable, SEARCH_FAST, "--query", query]
    p = subprocess.run(
        cmd,
        cwd=PHASE11_DIR,
        capture_output=True,
        text=True
    )

    if p.returncode != 0:
        raise RuntimeError(
            "gateway_search_fast failed: rc="
            + str(p.returncode)
            + " stderr="
            + (p.stderr or "")
            + " stdout="
            + (p.stdout or "")
        )

    out = (p.stdout or "").strip()
    if out == "":
        raise RuntimeError("gateway_search_fast returned empty stdout")

    try:
        obj = json.loads(out)
    except Exception as e:
        raise RuntimeError("gateway_search_fast returned non-JSON stdout: " + str(e) + " raw=" + repr(out)) from e

    return obj

def build_proof(ids: List[str], batch: List[Dict[str, Any]]) -> Dict[str, Any]:
    ids_hash = sha256_text("\n".join(ids))
    canonical_batch = json.dumps(batch, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    batch_hash = sha256_text(canonical_batch)
    return {"ids_count": len(ids), "ids_hash": ids_hash, "batch_hash": batch_hash}

def main() -> None:
    ap = argparse.ArgumentParser(description="Phase11 searchget: reuse gateway_search_fast then getbatch by ids")
    ap.add_argument("--query", required=True)
    ap.add_argument("--top", type=int, default=20)
    args = ap.parse_args()

    ensure_dir(OUTBOX_DIR)

    search_raw = run_search_fast(args.query)

    ids_all = search_raw.get("ids", [])
    if not isinstance(ids_all, list):
        raise RuntimeError("search_fast JSON has no 'ids' list")

    ids = [str(x) for x in ids_all][: max(0, int(args.top))]

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cols = get_event_columns(conn)

    batch: List[Dict[str, Any]] = []
    missing: List[str] = []

    for _id in ids:
        ev = fetch_event_by_id(conn, _id, cols)
        if ev is None:
            missing.append(_id)
            continue
        ev["integrity_recalc"] = integrity_recalc(ev)
        batch.append(ev)

    conn.close()

    proof = build_proof(ids, batch)

    snapshot = {
        "query": args.query,
        "top": args.top,
        "generated_at_utc": utc_now_iso(),
        "search_fast_raw": search_raw,
        "fixed_ids_order": ids,
        "missing_ids": missing
    }

    snapshot_json = json.dumps(snapshot, ensure_ascii=False, indent=2)
    snapshot_hash = sha256_text(snapshot_json)

    output = {
        "mode": "searchget",
        "generated_at_utc": utc_now_iso(),
        "search_snapshot": snapshot,
        "snapshot_hash": snapshot_hash,
        "fixed_ids_order": ids,
        "missing_ids": missing,
        "proof": proof,
        "batch": batch
    }

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(OUTBOX_DIR, f"searchget_{ts}.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("OUTPUT_JSON:", out_path)
    if missing:
        print("MISSING_IDS_COUNT:", len(missing))

if __name__ == "__main__":
    main()
