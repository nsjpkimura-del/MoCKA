import os
import sys
import sqlite3
import json
import hashlib
from datetime import datetime
from openpyxl import Workbook

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "knowledge.db")
OUTBOX_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../outbox"))

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def generate_integrity_proof(payload: dict) -> str:
    payload_str = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return sha256_text(payload_str)

def fetch_record(sha_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, timestamp, source, category, summary, raw_text, tags, hash
        FROM events
        WHERE id = ?
    """, (sha_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    keys = [
        "id",
        "timestamp",
        "source",
        "category",
        "summary",
        "raw_text",
        "tags",
        "hash"
    ]

    return dict(zip(keys, row))

def export_xlsx(record, integrity_proof):
    os.makedirs(OUTBOX_DIR, exist_ok=True)

    wb = Workbook()
    ws = wb.active
    ws.title = "MoCKA_Record"

    headers = [
        "id",
        "timestamp",
        "source",
        "category",
        "summary",
        "tags",
        "preview",
        "integrity_proof"
    ]

    ws.append(headers)

    raw_text = record.get("raw_text", "")
    preview = raw_text[:500] if raw_text else ""

    ws.append([
        record.get("id"),
        record.get("timestamp"),
        record.get("source"),
        record.get("category"),
        record.get("summary"),
        record.get("tags"),
        preview,
        integrity_proof
    ])

    timestamp_now = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"get_{record.get('id')}_{timestamp_now}.xlsx"
    path = os.path.join(OUTBOX_DIR, filename)

    wb.save(path)
    return path

def main():
    if len(sys.argv) < 2:
        print("Usage: python gateway_get.py <sha_id>")
        sys.exit(1)

    sha_id = sys.argv[1].strip()

    record = fetch_record(sha_id)

    if not record:
        print("ID not found.")
        sys.exit(1)

    integrity_proof = generate_integrity_proof(record)
    xlsx_path = export_xlsx(record, integrity_proof)

    result = {
        "status": "GET_OK",
        "payload": record,
        "integrity_proof": integrity_proof,
        "xlsx_path": xlsx_path
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
