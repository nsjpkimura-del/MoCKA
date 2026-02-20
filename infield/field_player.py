from __future__ import annotations

import os
import time
from typing import Any, Dict

from src.mocka_ai import call_ai
from src.mocka_outbox import OutboxEvent, write_outbox, now_epoch_ms, new_run_id
from src.mocka_memory import append_experiment, get_last_experiment, get_stats
from src.mocka_policy import decide


def _env_snapshot() -> Dict[str, Any]:
    keys = [
        "MOCKA_ALLOW_TYPE",
        "MOCKA_ALLOW_KEY",
        "MOCKA_ALLOW_AI",
        "MOCKA_PROVIDER",
        "MOCKA_MODEL",
        "MOCKA_CYCLES",
        "MOCKA_TASK",
    ]
    return {k: os.environ.get(k) for k in keys}


def _allowed_flags(env: Dict[str, Any]) -> Dict[str, bool]:
    return {
        "type": env.get("MOCKA_ALLOW_TYPE") == "1",
        "key": env.get("MOCKA_ALLOW_KEY") == "1",
        "ai": env.get("MOCKA_ALLOW_AI") == "1",
    }


def _sha256_text(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_one_cycle(task_text: str, cycle_index: int = 0) -> str:
    run_id = new_run_id()
    stage = f"cycle_{cycle_index}"

    start_ms = now_epoch_ms()
    env = _env_snapshot()
    allowed = _allowed_flags(env)
    task_sha256 = _sha256_text(task_text)

    prev = get_last_experiment(task_sha256)
    stats = get_stats(task_sha256)
    policy = decide(env, allowed, prev, stats)

    try:
        # Test hook: force exception for self-repair validation
        if os.environ.get("MOCKA_RAISE_TEST") == "1":
            raise RuntimeError("forced_test_exception")

        ai = call_ai(task_text)

        ok = bool(ai.ok)
        summary = "ai_ok" if ok else "ai_fail"
        error = None if ok else {"message": ai.error}

    except Exception as e:
        ok = False
        summary = "exception"
        error = {"message": str(e)}

    end_ms = now_epoch_ms()
    elapsed_ms = end_ms - start_ms

    event = OutboxEvent(
        schema="mocka.outbox.v1",
        run_id=run_id,
        ts_ms=start_ms,
        stage=stage,
        ok=ok,
        summary=summary,
        data={
            "task_text": task_text,
            "task_sha256": task_sha256,
            "cycle_index": cycle_index,
            "env": env,
            "allowed": allowed,
            "timing": {
                "start_ms": start_ms,
                "end_ms": end_ms,
                "elapsed_ms": elapsed_ms,
            },
            "memory_ref": {
                "prev": prev,
                "stats": stats,
            },
            "policy": policy,
        },
        error=error,
    )

    out_path = write_outbox(event)

    append_experiment({
        "schema": "mocka.memory.experiment.v1",
        "run_id": run_id,
        "stage": stage,
        "ok": ok,
        "summary": summary,
        "task_sha256": task_sha256,
        "cycle_index": cycle_index,
        "ts_ms": start_ms,
        "elapsed_ms": elapsed_ms,
        "allowed": allowed,
        "provider": env.get("MOCKA_PROVIDER"),
        "model": env.get("MOCKA_MODEL"),
        "outbox_path": out_path,
    })

    return out_path
