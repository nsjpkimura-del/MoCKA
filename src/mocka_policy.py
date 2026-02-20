from __future__ import annotations

import os
from typing import Any, Dict, List, Optional


def _get_int(name: str, default: int) -> int:
    v = os.environ.get(name, "").strip()
    if not v:
        return default
    try:
        return int(v)
    except Exception:
        return default


def decide(env: Dict[str, Any], allowed: Dict[str, Any], prev: Optional[Dict[str, Any]], stats: Dict[str, Any]) -> Dict[str, Any]:
    notes: List[str] = []
    decision = "normal"
    sleep_ms = 0

    # Test hook: force cooldown sleep for validation
    force = os.environ.get("MOCKA_POLICY_FORCE_COOLDOWN_MS", "").strip()
    if force:
        try:
            v = int(force)
        except Exception:
            v = 0
        if v > 0:
            notes.append("force_cooldown")
            if not bool(allowed.get("ai")):
                notes.append("ai_locked")
            return {
                "schema": "mocka.policy.v1",
                "decision": "cooldown",
                "sleep_ms": int(v),
                "notes": notes,
            }

    
    # Test hook: force decision for validation
    force_dec = os.environ.get("MOCKA_POLICY_FORCE_DECISION", "").strip().lower()
    if force_dec in ("halt", "cooldown", "normal"):
        notes.append("force_decision")
        if not bool(allowed.get("ai")):
            notes.append("ai_locked")
        # keep sleep_ms from other rules if already set; here we return immediately
        return {
            "schema": "mocka.policy.v1",
            "decision": force_dec,
            "sleep_ms": int(sleep_ms),
            "notes": notes,
        }
# Configurable repair knobs
    repair_sleep_ms = _get_int("MOCKA_REPAIR_SLEEP_MS", 800)
    halt_after_exceptions = _get_int("MOCKA_HALT_AFTER_EXCEPTIONS", 3)

    # Rule 0: no history yet -> do not penalize
    n = stats.get("n", 0)
    try:
        n_i = int(n)
    except Exception:
        n_i = 0

    if n_i == 0:
        notes.append("no_history")
        if not bool(allowed.get("ai")):
            notes.append("ai_locked")
        return {
            "schema": "mocka.policy.v1",
            "decision": decision,
            "sleep_ms": int(sleep_ms),
            "notes": notes,
        }

    # Rule R1: self-repair on previous exception
    if prev and str(prev.get("summary")) == "exception":
        decision = "cooldown"
        sleep_ms = max(sleep_ms, repair_sleep_ms)
        notes.append("self_repair_prev_exception")

    # Rule R2: halt suggestion when consecutive exceptions exceed threshold
    # We approximate consecutive exceptions by using stats.ok_rate with small n, plus last result.
    # For stronger accuracy, a dedicated "consecutive exception counter" will be added later.
    if prev and str(prev.get("summary")) == "exception":
        # if we have very low ok_rate and some history, treat as repeated failures
        ok_rate = stats.get("ok_rate", 1.0)
        try:
            ok_rate_f = float(ok_rate)
        except Exception:
            ok_rate_f = 1.0
        n_hist = int(stats.get("n", 0) or 0)

        # conservative: if last is exception AND ok_rate is 0 AND history length >= threshold
        if ok_rate_f == 0.0 and n_hist >= halt_after_exceptions:
            decision = "halt"
            sleep_ms = max(sleep_ms, repair_sleep_ms)
            notes.append("halt_suggested_repeated_exceptions")

    # Rule 2: low ok_rate -> cooldown
    ok_rate = stats.get("ok_rate", 1.0)
    try:
        ok_rate_f = float(ok_rate)
    except Exception:
        ok_rate_f = 1.0

    if ok_rate_f < 0.5:
        decision = "cooldown"
        sleep_ms = max(sleep_ms, 500)
        notes.append("low_ok_rate")

    if not bool(allowed.get("ai")):
        notes.append("ai_locked")

    return {
        "schema": "mocka.policy.v1",
        "decision": decision,
        "sleep_ms": int(sleep_ms),
        "notes": notes,
    }

