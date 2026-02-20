import os
import json
import csv
import hashlib
import sqlite3
import argparse
from datetime import datetime, timezone
import openpyxl

BASE = r"C:\Users\sirok\MoCKA"
PHASE11 = os.path.join(BASE, "infield", "phase11")
OUTBOX  = os.path.join(BASE, "outbox")
RAW_PATH = os.path.join(PHASE11, "raw_events.jsonl")
CSV_PATH = os.path.join(PHASE11, "structured.csv")
DB_PATH  = os.path.join(PHASE11, "knowledge.db")

HEADER = ["id","timestamp","source","category","summary","raw_text","tags","hash"]

def sha256_text(t):
    return hashlib.sha256(t.encode("utf-8")).hexdigest()

def sha256_bytes(b):
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def connect_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=NORMAL;")
    cur.execute("PRAGMA temp_store=MEMORY;")
    cur.execute("PRAGMA wal_autocheckpoint=1000;")
    cur.execute("PRAGMA busy_timeout=3000;")
    cur.execute("PRAGMA mmap_size=268435456;")
    return con

def ensure_structured_header():
    if not os.path.isfile(CSV_PATH):
        with open(CSV_PATH, "w", encoding="ascii", newline="") as f:
            csv.writer(f).writerow(HEADER)

def gateway_save(source, category, summary, raw_text, tags, no_xlsx=False):

    ts = datetime.now(timezone.utc).isoformat()
    content_hash = sha256_text(raw_text)
    record_id = sha256_text("|".join([content_hash, source, category, tags]))

    event = {
        "id": record_id,
        "timestamp": ts,
        "source": source,
        "category": category,
        "summary": summary,
        "raw_text": raw_text,
        "tags": tags,
        "hash": content_hash
    }

    # raw append
    os.makedirs(os.path.dirname(RAW_PATH), exist_ok=True)
    with open(RAW_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    # structured append
    ensure_structured_header()
    with open(CSV_PATH, "a", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow([event[k] for k in HEADER])

    # sqlite insert (dedupe)
    con = connect_db()
    cur = con.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO events (id,timestamp,source,category,summary,raw_text,tags,hash) VALUES (?,?,?,?,?,?,?,?)",
        (record_id, ts, source, category, summary, raw_text, tags, content_hash)
    )
    con.commit()
    con.close()

    os.makedirs(OUTBOX, exist_ok=True)

    xlsx_path = None
    if not no_xlsx:
        xlsx_path = os.path.join(OUTBOX, f"{record_id}.xlsx")
        wb = openpyxl.Workbook()
        ws_meta = wb.active
        ws_meta.title = "meta"
        ws_meta.append(["key","value"])
        for k,v in [
            ("id",record_id),
            ("timestamp_utc",ts),
            ("source",source),
            ("category",category),
            ("tags",tags),
            ("hash",content_hash)
        ]:
            ws_meta.append([k,v])

        ws = wb.create_sheet("event")
        ws.append(HEADER)
        ws.append([event[k] for k in HEADER])
        wb.save(xlsx_path)

    # payload bytes once (no reread)
    payload_bytes = json.dumps(event, ensure_ascii=False, indent=2).encode("utf-8")
    payload_sha = sha256_bytes(payload_bytes)

    payload_path = os.path.join(OUTBOX, f"{record_id}_payload.json")
    with open(payload_path, "wb") as f:
        f.write(payload_bytes)

    proof = {
        "kind": "save",
        "id": record_id,
        "timestamp": ts,
        "payload_file": os.path.basename(payload_path),
        "payload_sha256": payload_sha,
        "xlsx_file": os.path.basename(xlsx_path) if xlsx_path else None,
        "xlsx_sha256": sha256_file(xlsx_path) if xlsx_path else None,
        "dedupe_rule": "id = sha256(content_hash|source|category|tags)",
    }

    proof_path = os.path.join(OUTBOX, f"{record_id}_integrity_proof.json")
    with open(proof_path, "w", encoding="utf-8") as f:
        json.dump(proof, f, ensure_ascii=False, indent=2)

    print("SAVE_OK:", record_id)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="manual")
    ap.add_argument("--category", default="phase11")
    ap.add_argument("--summary", default="no_summary")
    ap.add_argument("--raw_text", default="no_text")
    ap.add_argument("--tags", default="phase11")
    ap.add_argument("--no_xlsx", action="store_true")
    a = ap.parse_args()

    gateway_save(
        a.source,
        a.category,
        a.summary,
        a.raw_text,
        a.tags,
        no_xlsx=a.no_xlsx
    )
