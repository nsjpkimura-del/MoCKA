from __future__ import annotations

import os
import time

import sys
sys.path.insert(0, r"")
from field_player import run_one_cycle


def getenv_int(name: str, default: int) -> int:
    v = os.environ.get(name, str(default)).strip()
    try:
        return int(v)
    except Exception:
        return default


def main() -> int:
    cycles = getenv_int("MOCKA_CYCLES", 1)
    sleep_ms = getenv_int("MOCKA_SLEEP_MS", 0)
    task_text = os.environ.get("MOCKA_TASK", "manual_task")

    rc = 0
    for i in range(cycles):
        try:
            out_path = run_one_cycle(task_text=task_text, cycle_index=i)
            print(f"[main_loop] cycle={i} outbox={out_path}")
        except Exception as e:
            rc = 1
            print(f"[main_loop] cycle={i} exception={e}")
        if sleep_ms > 0:
            time.sleep(sleep_ms / 1000.0)

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
