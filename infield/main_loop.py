from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

# ---- Import stabilization (Windows-safe) ----
# `python -m infield.main_loop` でも `python infield/main_loop.py` でも動くようにする保険。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
# --------------------------------------------

from src.mocka_audit.audit_writer import AuditWriter, sha256_bytes_hex, sha256_file_hex  # noqa: E402


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _ensure_dir(p: str) -> None:
    Path(p).mkdir(parents=True, exist_ok=True)


def _write_outbox_json(outbox_dir: str, payload: Dict[str, Any]) -> str:
    _ensure_dir(outbox_dir)
    ts_ms = int(time.time() * 1000)
    out_path = Path(outbox_dir) / f"{ts_ms}_event.json"
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    return str(out_path)


def main() -> int:
    outbox_dir = os.environ.get("MOCKA_OUTBOX_DIR", "outbox")
    audit_dir = os.environ.get("MOCKA_AUDIT_DIR", "audit")
    source_path = os.environ.get("MOCKA_SOURCE_PATH", "").strip()

    payload = {
        "ts": _now_utc_iso(),
        "event_kind": "ingest",
        "note": "phase12 week1 smoke run",
    }

    if source_path and Path(source_path).exists():
        source_hash = sha256_file_hex(source_path)
    else:
        source_hash = sha256_bytes_hex(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        )

    # 1) outbox 書き込み（確定点）
    outbox_path = _write_outbox_json(outbox_dir, payload)

    # 2) outbox 書き込み成功後に after_hash
    after_hash = sha256_file_hex(outbox_path)

    # 3) 監査イベント生成と保存
    audit = AuditWriter(audit_dir=audit_dir)
    rec = audit.write_event(
        event_kind="ingest",
        target_path=outbox_path,
        sha256_source=source_hash,
        sha256_after=after_hash,
    )

    print("OK")
    print("outbox_path:", outbox_path)
    print("audit_event_id:", rec["event_id"])
    print("audit_chain_hash:", rec["chain_hash"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())