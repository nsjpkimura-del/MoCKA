#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gateway_audit_search.py (Phase11)

Audit log search gate for outbox file_edit / file_restore logs.

Design goals:
- Stable enumeration of outbox logs for Windows
- Robust JSON loading (UTF-8 BOM, minor .js wrappers)
- Correct target extraction across schema variants
  - v1: {"target_file": "..."}
  - v2: {"target": {"path": "...", "file_name": "..."}}
- Deterministic output JSON saved in outbox
- Debug observability: scanned files, parse success/failure, filter decisions

Usage example:
  cd C:\\Users\\sirok\\MoCKA\\infield\\phase11
  python .\\gateway_audit_search.py --type edit --file gateway_audit_search.py --top 10 --debug
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

OUTBOX_DIR_DEFAULT = r"C:\Users\sirok\MoCKA\outbox"


def utc_stamp() -> str:
    return dt.datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def safe_abspath(p: str) -> str:
    return os.path.abspath(os.path.expandvars(os.path.expanduser(p)))


def collect_logs(outbox_dir: str, mode: str) -> List[str]:
    patterns: List[str] = []
    if mode in ("edit", "all"):
        patterns.extend(["file_edit_*.json", "file_edit_*.js", "file_edit_*.js*"])
    if mode in ("restore", "all"):
        patterns.extend(["file_restore_*.json", "file_restore_*.js", "file_restore_*.js*"])

    paths: List[str] = []
    for pat in patterns:
        paths.extend(glob.glob(os.path.join(outbox_dir, pat)))

    # De-duplicate, then sort newest first by mtime (best-effort)
    uniq = list({safe_abspath(p) for p in paths if os.path.isfile(p)})
    try:
        uniq.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    except Exception:
        uniq.sort(reverse=True)
    return uniq


def read_text_best_effort(path: str) -> Tuple[bool, str, Optional[str]]:
    """
    Read file as text robustly. Handles UTF-8 BOM. Falls back to cp932 with replacement.
    Returns (ok, text, err).
    """
    try:
        with open(path, "rb") as f:
            b = f.read()

        if b.startswith(b"\xef\xbb\xbf"):
            b = b[3:]

        try:
            return True, b.decode("utf-8"), None
        except UnicodeDecodeError:
            return True, b.decode("cp932", errors="replace"), None
    except Exception as e:
        return False, "", f"read_error: {type(e).__name__}: {e}"


_JS_PREFIXES = [
    re.compile(r"^\s*export\s+default\s+", re.IGNORECASE),
    re.compile(r"^\s*module\.exports\s*=\s*", re.IGNORECASE),
    re.compile(r"^\s*exports\.default\s*=\s*", re.IGNORECASE),
]


def strip_js_wrappers(text: str) -> str:
    t = text.strip()

    for rx in _JS_PREFIXES:
        t2 = rx.sub("", t, count=1).strip()
        if t2 != t:
            t = t2
            break

    if t.endswith(";"):
        t = t[:-1].rstrip()

    # Conservative object literal extraction: first '{' to last '}'
    if not t.startswith("{") and "{" in t and "}" in t:
        i = t.find("{")
        j = t.rfind("}")
        if 0 <= i < j:
            t = t[i : j + 1].strip()

    return t


def load_json_any(path: str) -> Tuple[bool, Optional[Any], str, str]:
    """
    Attempts to parse JSON from file.
    Returns (ok, obj, mode, err)
      mode: json | js-unwrapped | jsonlines | none
    """
    ok_read, raw, err = read_text_best_effort(path)
    if not ok_read:
        return False, None, "none", err or "read_failed"

    s = raw.strip()

    # 1) plain json
    try:
        return True, json.loads(s), "json", ""
    except Exception as e1:
        err1 = f"json_parse_error: {type(e1).__name__}: {e1}"

    # 2) js-unwrapped json
    s2 = strip_js_wrappers(s)
    if s2 != s:
        try:
            return True, json.loads(s2), "js-unwrapped", ""
        except Exception as e2:
            err2 = f"js_unwrapped_parse_error: {type(e2).__name__}: {e2}"
    else:
        err2 = ""

    # 3) json lines recovery
    lines = [ln.strip() for ln in s.splitlines() if ln.strip()]
    if len(lines) >= 2:
        objs: List[Any] = []
        any_ok = False
        last_err = ""
        for ln in lines:
            try:
                objs.append(json.loads(ln))
                any_ok = True
            except Exception as e3:
                last_err = f"jsonlines_parse_error: {type(e3).__name__}: {e3}"
        if any_ok:
            return True, objs, "jsonlines", ""
        if last_err:
            return False, None, "jsonlines", last_err

    # fall back: return best error
    if err2:
        return False, None, "none", f"{err1} | {err2}"
    return False, None, "none", err1


def normalize_events(obj: Any) -> List[Dict[str, Any]]:
    if isinstance(obj, dict):
        return [obj]
    if isinstance(obj, list):
        out: List[Dict[str, Any]] = []
        for it in obj:
            if isinstance(it, dict):
                out.append(it)
        return out
    return []


def target_text(obj: Dict[str, Any]) -> str:
    """
    Target extraction that matches actual safe_edit schema first, then backward/forward compatible variants.
    Priority:
      1) obj["target_file"] (safe_edit current schema)
      2) obj["target"]["path"] + obj["target"]["file_name"] (nested schema)
      3) fallbacks: filename, file, path, target_path
    """
    if not isinstance(obj, dict):
        return ""

    v = obj.get("target_file")
    if v:
        return str(v).lower()

    t = obj.get("target")
    if isinstance(t, dict):
        p = t.get("path") or ""
        fn = t.get("file_name") or ""
        merged = (str(p) + " " + str(fn)).strip()
        if merged:
            return merged.lower()

    for k in ("filename", "file", "path", "target_path"):
        v2 = obj.get(k)
        if v2:
            return str(v2).lower()

    return ""


def note_text(obj: Dict[str, Any]) -> str:
    if not isinstance(obj, dict):
        return ""
    return str(obj.get("note", "") or "").lower()


def event_type_text(obj: Dict[str, Any]) -> str:
    if not isinstance(obj, dict):
        return ""
    return str(obj.get("event_type", "") or "").strip().lower()


def passes_type_filter(obj: Dict[str, Any], mode: str) -> bool:
    et = event_type_text(obj)
    if mode == "edit":
        return et == "file_edit"
    if mode == "restore":
        return et == "file_restore"
    return True  # all


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outbox", default=OUTBOX_DIR_DEFAULT)
    ap.add_argument("--type", default="all", choices=["all", "edit", "restore"])
    ap.add_argument("--file", default="", help="substring filter on target_text()")
    ap.add_argument("--note", default="", help="substring filter on note")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args(argv)

    outbox = safe_abspath(args.outbox)
    mode = args.type.lower()
    file_sub = (args.file or "").lower()
    note_sub = (args.note or "").lower()
    top = max(1, int(args.top))

    paths = collect_logs(outbox, mode)

    debug_files: List[Dict[str, Any]] = []
    parse_errors: List[Dict[str, Any]] = []
    scanned_events = 0

    results: List[Dict[str, Any]] = []

    for p in paths:
        file_info: Dict[str, Any] = {
            "log_file": os.path.basename(p),
            "path": p,
            "size_bytes": None,
            "parse_ok": False,
            "parse_mode": None,
            "events_in_file": 0,
            "matched_in_file": 0,
        }
        try:
            file_info["size_bytes"] = os.path.getsize(p)
        except Exception:
            file_info["size_bytes"] = None

        ok, obj, mode_parse, err = load_json_any(p)
        file_info["parse_ok"] = ok
        file_info["parse_mode"] = mode_parse

        if not ok:
            parse_errors.append({"log_file": os.path.basename(p), "path": p, "error": err, "mode": mode_parse})
            debug_files.append(file_info)
            continue

        events = normalize_events(obj)
        file_info["events_in_file"] = len(events)
        scanned_events += len(events)

        matched_here = 0
        for ev in events:
            if not passes_type_filter(ev, mode):
                continue

            tgt = target_text(ev)
            nt = note_text(ev)

            if file_sub and file_sub not in tgt:
                continue
            if note_sub and note_sub not in nt:
                continue

            # produce normalized result row
            results.append(
                {
                    "timestamp": ev.get("timestamp") or ev.get("ts_utc") or ev.get("generated_at"),
                    "event_type": ev.get("event_type"),
                    "note": ev.get("note"),
                    "target_file": ev.get("target_file") or (ev.get("target", {}) or {}).get("file_name"),
                    "target_path": (ev.get("target", {}) or {}).get("path"),
                    "log_file": os.path.basename(p),
                }
            )
            matched_here += 1
            if len(results) >= top:
                break

        file_info["matched_in_file"] = matched_here
        debug_files.append(file_info)

        if len(results) >= top:
            break

    ts = utc_stamp()
    out_payload: Dict[str, Any] = {
        "event_type": "auditsearch_result",
        "generated_at_utc": ts,
        "outbox": outbox,
        "query": {"type": mode, "file_substring": args.file, "note_substring": args.note, "top": top},
        "scanned_file_count": len(paths),
        "scanned_event_count": scanned_events,
        "parse_error_count": len(parse_errors),
        "result_count": len(results),
        "results": results,
    }

    if args.debug:
        out_payload["debug"] = {
            "scanned_files": [os.path.basename(p) for p in paths],
            "file_stats": debug_files,
            "parse_errors": parse_errors,
            "filter_observation_sample": [
                {
                    "log_file": fi["log_file"],
                    "parse_ok": fi["parse_ok"],
                    "parse_mode": fi["parse_mode"],
                    "events_in_file": fi["events_in_file"],
                    "matched_in_file": fi["matched_in_file"],
                }
                for fi in debug_files[:10]
            ],
        }

    # Always output as .json (extension fixed)
    os.makedirs(outbox, exist_ok=True)
    out_path = os.path.join(outbox, f"file_auditsearch_{ts}.json")
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out_payload, f, ensure_ascii=False, indent=2)

    # Print only the output path (wrapper-friendly)
    sys.stdout.write(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
