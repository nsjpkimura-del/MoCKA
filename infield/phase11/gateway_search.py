import os
import csv
import json
import sqlite3
import openpyxl
import hashlib
import argparse
from datetime import datetime, timezone

BASE = r"C:\Users\sirok\MoCKA"
PHASE11 = os.path.join(BASE, "infield", "phase11")
OUTBOX  = os.path.join(BASE, "outbox")
DB_PATH = os.path.join(PHASE11, "knowledge.db")


def sha256_file(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def gateway_search(query, limit=20):
    ts = datetime.now(timezone.utc).isoformat()
    qid = sha256_text("search:" + query + ":" + ts)

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # Use FTS if available
    cur.execute("""
        SELECT e.id, e.timestamp, e.source, e.category, e.summary, e.raw_text, e.tags, e.hash
        FROM events_fts f
        JOIN events e ON e.rowid = f.rowid
        WHERE events_fts MATCH ?
        ORDER BY e.timestamp DESC
        LIMIT ?
    """, (query, limit))
    rows = cur.fetchall()
    con.close()

    # 1) outbox excel-compatible csv
# 1) outbox excel export (xlsx)
    out_xlsx = os.path.join(OUTBOX, f"search_{qid}.xlsx")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "results"
    ws.append(["id","timestamp","source","category","summary","raw_text","tags","hash"])
    for r in rows:
        ws.append(list(r))
    wb.save(out_xlsx)

# 2) evidence payload + integrity proof (json)
    payload = {
        "kind": "search",
        "search_id": qid,
        "timestamp": ts,
        "query": query,
        "limit": limit,
        "hits": len(rows),
        "xlsx_file": os.path.basename(out_xlsx),
    }

    payload_path = os.path.join(OUTBOX, f"search_{qid}_payload.json")
    with open(payload_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    proof = {
        "kind": "search",
        "search_id": qid,
        "timestamp": ts,
        "payload_file": os.path.basename(payload_path),
        "payload_sha256": sha256_file(payload_path),
        "xlsx_file": os.path.basename(out_xlsx),
        "xlsx_sha256": sha256_file(out_xlsx),
    }

    proof_path = os.path.join(OUTBOX, f"search_{qid}_integrity_proof.json")
    with open(proof_path, "w", encoding="utf-8") as f:
        json.dump(proof, f, ensure_ascii=False, indent=2)

    print("SEARCH_OK:", qid, "HITS:", len(rows))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=False, default="phase11 OR Phase11 OR test")
    ap.add_argument("--limit", required=False, type=int, default=20)
    args = ap.parse_args()
    gateway_search(args.query, limit=args.limit)
