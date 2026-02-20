from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Dict, Optional

from src.mocka_audit.contract_v1 import AuditEventInput, derive_event, validate_derived
from src.mocka_audit.db_schema import LEDGER_TABLE, connect, ensure_audit_ledger_table


def sha256_file_hex(path: str) -> str:
    p = Path(path)
    h = sha256()
    with p.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes_hex(data: bytes) -> str:
    return sha256(data).hexdigest()


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class AuditWriter:
    def __init__(
        self,
        audit_dir: str = "audit",
        audit_db_path: Optional[str] = None,
    ):
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.last_event_id_path = self.audit_dir / "last_event_id.txt"

        self.audit_db_path = audit_db_path or os.environ.get(
            "MOCKA_AUDIT_DB_PATH",
            r"infield\phase11\db\knowledge.db",
        )

    def _get_previous_event_id(self) -> str:
        if not self.last_event_id_path.exists():
            return "GENESIS"
        s = self.last_event_id_path.read_text(encoding="utf-8").strip()
        return s if s else "GENESIS"

    def _set_previous_event_id(self, event_id: str) -> None:
        self.last_event_id_path.write_text(event_id, encoding="utf-8")

    def _persist_json(self, record: Dict[str, str]) -> None:
        out_path = self.audit_dir / f"{record['event_id']}.json"
        out_path.write_text(
            json.dumps(record, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )

    def _persist_db_ledger(self, record: Dict[str, str]) -> None:
        conn = connect(self.audit_db_path)
        try:
            ensure_audit_ledger_table(conn)
            conn.execute(
                f"""
                INSERT OR IGNORE INTO {LEDGER_TABLE}(
                    event_id, chain_hash, previous_event_id, event_content, contract_version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    record["event_id"],
                    record["chain_hash"],
                    record["previous_event_id"],
                    record["event_content"],
                    record["contract_version"],
                    record["created_at"],
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def write_event(
        self,
        *,
        event_kind: str,
        target_path: str,
        sha256_source: str,
        sha256_after: str,
        contract_version: str = "mocka.audit.v1",
        ts_local: Optional[datetime] = None,
    ) -> Dict[str, str]:
        prev = self._get_previous_event_id()
        ts = ts_local if ts_local is not None else datetime.now(timezone.utc)

        inp = AuditEventInput(
            ts_local=ts,
            event_kind=event_kind,
            target_path=str(target_path),
            sha256_source=sha256_source,
            sha256_after=sha256_after,
            contract_version=contract_version,
        )

        derived = derive_event(inp, previous_event_id=prev)
        validate_derived(derived)

        record = {
            "event_content": derived.event_content,
            "event_id": derived.event_id,
            "chain_hash": derived.chain_hash,
            "contract_version": contract_version,
            "previous_event_id": prev,
            "created_at": _now_utc_iso(),
        }

        self._persist_json(record)
        self._persist_db_ledger(record)
        self._set_previous_event_id(derived.event_id)

        return record