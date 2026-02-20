from __future__ import annotations

import os
from datetime import datetime, timezone

from src.mocka_audit.db_schema import (
    AUDIT_SCHEMA_NAME,
    AUDIT_SCHEMA_VERSION,
    apply_audit_schema_v1,
    connect,
    get_schema_version,
)


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> int:
    db_path = os.environ.get(
        "MOCKA_AUDIT_DB_PATH",
        r"infield\phase11\db\knowledge.db",
    )

    applied_at = _now_utc_iso()

    conn = connect(db_path)
    try:
        cur_ver = get_schema_version(conn, AUDIT_SCHEMA_NAME)

        if cur_ver >= AUDIT_SCHEMA_VERSION:
            print("OK: schema up-to-date")
            print("db:", db_path)
            print("schema:", AUDIT_SCHEMA_NAME, "version:", cur_ver)
            return 0

        apply_audit_schema_v1(conn, applied_at=applied_at, note="migrate to mocka.audit v1")
        conn.commit()

        new_ver = get_schema_version(conn, AUDIT_SCHEMA_NAME)
        print("OK: schema migrated")
        print("db:", db_path)
        print("schema:", AUDIT_SCHEMA_NAME, "version:", new_ver)
        return 0

    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())