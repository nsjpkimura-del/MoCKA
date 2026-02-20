from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple


def _memory_dir() -> str:
    return os.environ.get("MOCKA_MEMORY_DIR", os.path.join(".", "memory"))


def _experiments_path() -> str:
    fname = os.environ.get("MOCKA_EXPERIMENT_LOG", "experiments.jsonl")
    return os.path.join(_memory_dir(), fname)


def ensure_memory_dir() -> str:
    d = _memory_dir()
    os.makedirs(d, exist_ok=True)
    return d


def append_experiment(record: Dict[str, Any]) -> str:
    ensure_memory_dir()
    path = _experiments_path()
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path


def save_kv(key: str, value: Any) -> str:
    ensure_memory_dir()
    safe_key = "".join([c if c.isalnum() or c in ("-", "_") else "_" for c in key])
    path = os.path.join(_memory_dir(), f"{safe_key}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"key": key, "value": value}, f, ensure_ascii=False, indent=2)
    return path


def load_kv(key: str) -> Optional[Any]:
    safe_key = "".join([c if c.isalnum() or c in ("-", "_") else "_" for c in key])
    path = os.path.join(_memory_dir(), f"{safe_key}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    return obj.get("value")


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                # ignore broken lines to keep the system robust
                continue
    return rows


def get_last_experiment(task_sha256: str) -> Optional[Dict[str, Any]]:
    path = _experiments_path()
    rows = _read_jsonl(path)
    for r in reversed(rows):
        if r.get("task_sha256") == task_sha256:
            # return a minimal, stable subset
            return {
                "run_id": r.get("run_id"),
                "stage": r.get("stage"),
                "ok": r.get("ok"),
                "summary": r.get("summary"),
                "ts_ms": r.get("ts_ms"),
                "elapsed_ms": r.get("elapsed_ms"),
                "allowed": r.get("allowed"),
                "provider": r.get("provider"),
                "model": r.get("model"),
                "outbox_path": r.get("outbox_path"),
            }
    return None


def get_stats(task_sha256: str) -> Dict[str, Any]:
    path = _experiments_path()
    rows = _read_jsonl(path)

    xs: List[Dict[str, Any]] = [r for r in rows if r.get("task_sha256") == task_sha256]
    n = len(xs)
    if n == 0:
        return {
            "n": 0,
            "ok_n": 0,
            "ok_rate": 0.0,
            "elapsed_ms_avg": None,
            "elapsed_ms_min": None,
            "elapsed_ms_max": None,
            "last_ts_ms": None,
        }

    ok_n = sum(1 for r in xs if bool(r.get("ok")))

    elapseds: List[int] = []
    for r in xs:
        v = r.get("elapsed_ms")
        if isinstance(v, int):
            elapseds.append(v)

    elapsed_avg = (sum(elapseds) / len(elapseds)) if elapseds else None
    elapsed_min = min(elapseds) if elapseds else None
    elapsed_max = max(elapseds) if elapseds else None

    last_ts = None
    for r in reversed(rows):
        if r.get("task_sha256") == task_sha256:
            last_ts = r.get("ts_ms")
            break

    return {
        "n": n,
        "ok_n": ok_n,
        "ok_rate": (ok_n / n),
        "elapsed_ms_avg": elapsed_avg,
        "elapsed_ms_min": elapsed_min,
        "elapsed_ms_max": elapsed_max,
        "last_ts_ms": last_ts,
    }
