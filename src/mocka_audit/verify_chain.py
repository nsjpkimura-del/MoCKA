from __future__ import annotations

import json
import os
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Dict, Tuple

from src.mocka_audit.db_schema import LEDGER_TABLE, connect


def _sha256_hex(s: str) -> str:
    return sha256(s.encode("utf-8")).hexdigest()


@dataclass
class AuditFileRecord:
    event_id: str
    chain_hash: str
    previous_event_id: str
    event_content: str


def load_audit_dir(audit_dir: str) -> Dict[str, AuditFileRecord]:
    p = Path(audit_dir)
    by_id: Dict[str, AuditFileRecord] = {}
    for f in p.glob("*.json"):
        obj = json.loads(f.read_text(encoding="utf-8"))
        r = AuditFileRecord(
            event_id=obj["event_id"],
            chain_hash=obj["chain_hash"],
            previous_event_id=obj["previous_event_id"],
            event_content=obj["event_content"],
        )
        by_id[r.event_id] = r
    return by_id


def verify_chain_from_files(audit_dir: str) -> Tuple[bool, str]:
    by_id = load_audit_dir(audit_dir)
    if not by_id:
        return False, "no audit json records"

    last_path = Path(audit_dir) / "last_event_id.txt"
    if not last_path.exists():
        return False, "missing last_event_id.txt"

    last_id = last_path.read_text(encoding="utf-8").strip()
    if last_id not in by_id:
        return False, f"last_event_id not found in json set: {last_id}"

    cur_id = last_id
    steps = 0
    while True:
        r = by_id[cur_id]

        if _sha256_hex(r.event_content) != r.event_id:
            return False, f"event_id mismatch at {r.event_id}"

        if _sha256_hex(r.previous_event_id + r.event_id) != r.chain_hash:
            return False, f"chain_hash mismatch at {r.event_id}"

        steps += 1
        if r.previous_event_id == "GENESIS":
            return True, f"OK: chain verified from files, length={steps}"

        if r.previous_event_id not in by_id:
            return False, f"missing previous_event_id json: {r.previous_event_id}"

        cur_id = r.previous_event_id


def verify_db_ledger(db_path: str) -> Tuple[bool, str]:
    conn = connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?;",
            (LEDGER_TABLE,),
        )
        if cur.fetchone() is None:
            return False, f"missing ledger table: {LEDGER_TABLE}"

        cur.execute(
            f"""
            SELECT event_id, chain_hash, previous_event_id, event_content
            FROM {LEDGER_TABLE}
            ORDER BY created_at ASC;
            """
        )
        rows = cur.fetchall()
        if not rows:
            return False, f"no rows in {LEDGER_TABLE}"

        for (eid, ch, peid, content) in rows:
            if _sha256_hex(content) != eid:
                return False, f"DB event_id mismatch: {eid}"
            if _sha256_hex(peid + eid) != ch:
                return False, f"DB chain_hash mismatch: {eid}"

        return True, f"OK: DB ledger verified, count={len(rows)}"
    finally:
        conn.close()


def main() -> int:
    audit_dir = os.environ.get("MOCKA_AUDIT_DIR", "audit")
    db_path = os.environ.get("MOCKA_AUDIT_DB_PATH", r"infield\phase11\db\knowledge.db")

    ok_f, msg_f = verify_chain_from_files(audit_dir)
    print(msg_f)

    ok_d, msg_d = verify_db_ledger(db_path)
    print(msg_d)

    return 0 if (ok_f and ok_d) else 2


if __name__ == "__main__":
    raise SystemExit(main())