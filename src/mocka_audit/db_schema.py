from __future__ import annotations

import sqlite3
from typing import Dict, Tuple


AUDIT_SCHEMA_NAME = "mocka.audit"
AUDIT_SCHEMA_VERSION = 1

LEDGER_TABLE = "audit_ledger_event"


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1;",
        (table,),
    )
    return cur.fetchone() is not None


def _columns(conn: sqlite3.Connection, table: str) -> Dict[str, Tuple[str, int, str]]:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table});")
    out: Dict[str, Tuple[str, int, str]] = {}
    for r in cur.fetchall():
        out[r[1]] = (r[2] or "", int(r[3] or 0), r[4] if r[4] is not None else "")
    return out


def ensure_schema_versions(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_versions (
            schema_name TEXT PRIMARY KEY,
            version INTEGER NOT NULL,
            applied_at TEXT NOT NULL,
            note TEXT NOT NULL
        );
        """
    )


def ensure_audit_ledger_table(conn: sqlite3.Connection) -> None:
    """
    Create Proof-Grade ledger table (new contract) without touching legacy audit_event.
    """
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {LEDGER_TABLE} (
            event_id TEXT PRIMARY KEY,
            chain_hash TEXT NOT NULL,
            previous_event_id TEXT NOT NULL DEFAULT 'GENESIS',
            event_content TEXT NOT NULL,
            contract_version TEXT NOT NULL DEFAULT 'mocka.audit.v1',
            created_at TEXT NOT NULL
        );
        """
    )
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{LEDGER_TABLE}_created_at ON {LEDGER_TABLE}(created_at);"
    )


def get_schema_version(conn: sqlite3.Connection, schema_name: str) -> int:
    if not _table_exists(conn, "schema_versions"):
        return 0
    cur = conn.cursor()
    cur.execute("SELECT version FROM schema_versions WHERE schema_name=?;", (schema_name,))
    row = cur.fetchone()
    return int(row[0]) if row else 0


def set_schema_version(conn: sqlite3.Connection, schema_name: str, version: int, applied_at: str, note: str) -> None:
    ensure_schema_versions(conn)
    conn.execute(
        """
        INSERT INTO schema_versions(schema_name, version, applied_at, note)
        VALUES(?, ?, ?, ?)
        ON CONFLICT(schema_name) DO UPDATE SET
            version=excluded.version,
            applied_at=excluded.applied_at,
            note=excluded.note;
        """,
        (schema_name, int(version), applied_at, note),
    )


def apply_audit_schema_v1(conn: sqlite3.Connection, applied_at: str, note: str = "init mocka.audit v1") -> None:
    """
    Week2: preserve legacy audit_event, introduce new ledger table.
    """
    ensure_schema_versions(conn)
    ensure_audit_ledger_table(conn)
    set_schema_version(conn, AUDIT_SCHEMA_NAME, AUDIT_SCHEMA_VERSION, applied_at, note)