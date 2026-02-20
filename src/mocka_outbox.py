from __future__ import annotations
import json
import os
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

def now_epoch_ms() -> int:
    return int(time.time() * 1000)

def new_run_id() -> str:
    return uuid.uuid4().hex

@dataclass
class OutboxEvent:
    schema: str
    run_id: str
    ts_ms: int
    stage: str
    ok: bool
    summary: str
    data: Dict[str, Any]
    error: Optional[Dict[str, Any]] = None

def write_outbox(event: OutboxEvent) -> str:
    out_dir = os.environ.get("MOCKA_OUTBOX_DIR", os.path.join(".", "outbox"))
    os.makedirs(out_dir, exist_ok=True)
    fname = f"{event.ts_ms}_{event.run_id}_{event.stage}.json"
    path = os.path.join(out_dir, fname)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(event), f, ensure_ascii=False, indent=2)
    return path
