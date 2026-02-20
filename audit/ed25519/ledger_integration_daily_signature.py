import argparse
import datetime
import json
import sqlite3
import hashlib
from daily_signature import sign_daily, build_daily_message

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def normalize_json_bytes(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")

def utc_now_z() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds").replace("+00:00", "Z")

def ensure_table(cur, table_name: str):
    cur.execute(f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      event_type TEXT NOT NULL,
      schema_version TEXT NOT NULL,
      event_content TEXT NOT NULL,
      event_id TEXT NOT NULL,
      prev_chain_hash TEXT,
      chain_hash TEXT NOT NULL,
      created_at_utc TEXT NOT NULL
    )
    """)

def get_last_chain_hash(cur, table_name: str) -> str:
    cur.execute(f"SELECT chain_hash FROM {table_name} ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    if not row or not row[0]:
        return ""
    return str(row[0])

def insert_daily_signature_event(
    db_path: str,
    table_name: str,
    schema_version: str,
    final_chain_hash: str,
    file_chain_length: int,
    ledger_count: int,
    date_str: str,
):
    signature_hex = sign_daily(date_str, final_chain_hash, file_chain_length, ledger_count)

    payload = {
        "date": date_str,
        "final_chain_hash": final_chain_hash,
        "file_chain_length": int(file_chain_length),
        "ledger_count": int(ledger_count),
        "signature_hex": signature_hex,
        "message_canonical": build_daily_message(date_str, final_chain_hash, file_chain_length, ledger_count).decode("utf-8"),
    }

    event_content_bytes = normalize_json_bytes(payload)
    event_content = event_content_bytes.decode("utf-8")
    event_id = sha256_hex(event_content_bytes)

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        ensure_table(cur, table_name)

        prev = get_last_chain_hash(cur, table_name)
        chain_hash = sha256_hex((prev + event_id).encode("utf-8"))

        cur.execute(
            f"""
            INSERT INTO {table_name}
            (event_type, schema_version, event_content, event_id, prev_chain_hash, chain_hash, created_at_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "daily_signature",
                schema_version,
                event_content,
                event_id,
                prev if prev != "" else None,
                chain_hash,
                utc_now_z(),
            ),
        )
        conn.commit()

        return {
            "event_type": "daily_signature",
            "schema_version": schema_version,
            "event_id": event_id,
            "prev_chain_hash": prev,
            "chain_hash": chain_hash,
        }
    finally:
        conn.close()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--table", default="audit_ledger_event")
    ap.add_argument("--schema-version", default="v1")
    ap.add_argument("--final-chain-hash", required=True)
    ap.add_argument("--file-chain-length", type=int, required=True)
    ap.add_argument("--ledger-count", type=int, required=True)
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    args = ap.parse_args()

    out = insert_daily_signature_event(
        db_path=args.db,
        table_name=args.table,
        schema_version=args.schema_version,
        final_chain_hash=args.final_chain_hash,
        file_chain_length=args.file_chain_length,
        ledger_count=args.ledger_count,
        date_str=args.date,
    )

    print(json.dumps(out, sort_keys=True, separators=(",", ":")))

if __name__ == "__main__":
    main()