import sqlite3
import datetime

def ensure_table(conn):
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_daily_signature (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            final_chain_hash TEXT NOT NULL,
            file_chain_length INTEGER NOT NULL,
            ledger_count INTEGER NOT NULL,
            signature_hex TEXT NOT NULL,
            created_at_utc TEXT NOT NULL
        )
        """
    )
    conn.commit()

def save_daily_signature(db_path, date_str, final_chain_hash, file_chain_length, ledger_count, signature_hex):
    conn = sqlite3.connect(db_path)
    try:
        ensure_table(conn)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO audit_daily_signature
            (date, final_chain_hash, file_chain_length, ledger_count, signature_hex, created_at_utc)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                date_str,
                final_chain_hash,
                int(file_chain_length),
                int(ledger_count),
                signature_hex,
                datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds") + "Z",
            ),
        )
        conn.commit()
    finally:
        conn.close()