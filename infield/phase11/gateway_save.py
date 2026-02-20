import os
import json
import csv
import hashlib
import argparse
import sqlite3
import openpyxl
from datetime import datetime, timezone

BASE = r"C:\Users\sirok\MoCKA"
PHASE11 = os.path.join(BASE, "infield", "phase11")
OUTBOX  = os.path.join(BASE, "outbox")

RAW_PATH = os.path.join(PHASE11, "raw_events.jsonl")
CSV_PATH = os.path.join(PHASE11, "structured.csv")
DB_PATH  = os.path.join(PHASE11, "knowledge.db")


def sha256_bytes(b):
    import hashlib
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()

def sha256_file(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def gateway_save(source, category, summary, raw_text, tags):

    timestamp = datetime.now(timezone.utc).isoformat()
    base_text = source + category + summary + raw_text + tags + timestamp
    record_id = sha256_text(base_text)
    record_hash = sha256_text(raw_text)

    event = {
        "id": record_id,
        "timestamp": timestamp,
        "source": source,
        "category": category,
        "summary": summary,
        "raw_text": raw_text,
        "tags": tags,
        "hash": record_hash
    }

    # 1 raw append
    with open(RAW_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    # 2 csv append
    file_exists = os.path.isfile(CSV_PATH)
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["id","timestamp","source","category","summary","raw_text","tags","hash"])
        writer.writerow([
            record_id,
            timestamp,
            source,
            category,
            summary,
            raw_text,
            tags,
            record_hash
        ])

    # 3 sqlite insert
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO events
        (id,timestamp,source,category,summary,raw_text,tags,hash)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        record_id,
        timestamp,
        source,
        category,
        summary,
        raw_text,
        tags,
        record_hash
    ))
    con.commit()
    con.close()

    # 4 excel export (csv as excel-compatible)
# 4 excel export (xlsx)
    excel_path = os.path.join(OUTBOX, f"{record_id}.xlsx")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "event"
    ws.append(["id","timestamp","source","category","summary","raw_text","tags","hash"])
    ws.append([
        record_id,
        timestamp,
        source,
        category,
        summary,
        raw_text,
        tags,
        record_hash
    ])
    wb.save(excel_path)

# 5 evidence payload + integrity proof (json)
    payload_path = os.path.join(OUTBOX, f"{record_id}_payload.json")
    with open(payload_path, "w", encoding="utf-8") as f:
        json.dump(event, f, ensure_ascii=False, indent=2)

    proof = {
        "kind": "save",
        "id": record_id,
        "timestamp": timestamp,
        "payload_file": os.path.basename(payload_path),
        "payload_sha256": sha256_file(payload_path),
        "xlsx_file": os.path.basename(excel_path),
        "xlsx_sha256": sha256_file(excel_path),
    }

    proof_path = os.path.join(OUTBOX, f"{record_id}_integrity_proof.json")
    with open(proof_path, "w", encoding="utf-8") as f:
        json.dump(proof, f, ensure_ascii=False, indent=2)

    print("SAVE_OK:", record_id)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=False, default="manual_test")
    ap.add_argument("--category", required=False, default="phase11")
    ap.add_argument("--summary", required=False, default="initial save test")
    ap.add_argument("--raw_text", required=False, default="This is a Phase11 test record.")
    ap.add_argument("--tags", required=False, default="phase11,test")
    args = ap.parse_args()

    gateway_save(
        source=args.source,
        category=args.category,
        summary=args.summary,
        raw_text=args.raw_text,
        tags=args.tags
    )
