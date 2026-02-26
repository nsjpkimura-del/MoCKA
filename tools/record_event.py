#!/usr/bin/env python3
import argparse
import csv
import datetime as dt
import hashlib
import os
import re
import subprocess
import sys
from typing import Dict, List, Tuple, Optional

RE_EVENT_ID = re.compile(r"^EVT-(\d{4})-(\d{6})$")


def die(msg: str, code: int = 1) -> None:
    sys.stderr.write(msg.rstrip() + "\n")
    raise SystemExit(code)


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.read()


def write_text(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def sha256_hex(s: str) -> str:
    h = hashlib.sha256()
    h.update(s.encode("utf-8"))
    return h.hexdigest()


def ensure_len(name: str, value: str, max_len: int) -> str:
    if len(value) > max_len:
        die(f"{name} too long: {len(value)} > {max_len}")
    if "\n" in value or "\r" in value:
        die(f"{name} must be single-line (no newlines)")
    return value


def today_iso() -> str:
    return dt.date.today().isoformat()


def parse_date(s: str) -> str:
    try:
        d = dt.date.fromisoformat(s)
    except Exception:
        die("invalid date, expected YYYY-MM-DD")
    return d.isoformat()


def read_index_header(index_path: str) -> str:
    with open(index_path, "r", encoding="utf-8", newline="") as f:
        h = f.readline()
    return h.lstrip("\ufeff").strip("\r\n").strip()


def load_index_rows(index_path: str) -> List[Dict[str, str]]:
    if not os.path.exists(index_path):
        die(f"index csv not found: {index_path}")

    with open(index_path, "r", encoding="utf-8", newline="") as f:
        raw = f.read()
    raw = raw.lstrip("\ufeff")
    lines = [ln for ln in raw.splitlines() if ln.strip() != ""]
    if not lines:
        die("index csv empty")

    header_line = lines[0].strip()
    data_lines = lines[1:]
    reader = csv.DictReader([header_line] + data_lines)

    if reader.fieldnames is None:
        die("index csv header missing")

    rows: List[Dict[str, str]] = []
    for row in reader:
        if not row:
            continue
        eid = (row.get("event_id") or "").strip()
        if eid == "":
            continue
        rows.append(row)
    return rows


def next_event_id(index_rows: List[Dict[str, str]], year: int) -> Tuple[str, int]:
    max_seq = 0
    y = str(year)
    for r in index_rows:
        eid = (r.get("event_id") or "").strip()
        m = RE_EVENT_ID.match(eid)
        if not m:
            continue
        if m.group(1) != y:
            continue
        seq = int(m.group(2))
        if seq > max_seq:
            max_seq = seq
    new_seq = max_seq + 1
    return f"EVT-{year:04d}-{new_seq:06d}", new_seq


def canonical_path_for(date_iso: str, seq: int) -> str:
    d = dt.date.fromisoformat(date_iso)
    yymmdd = d.strftime("%y%m%d")
    serial4 = seq % 10000
    return os.path.join("governance", "history", f"REC-{yymmdd}-{serial4:04d}.md")


def fill_template(tpl: str, mapping: Dict[str, str]) -> str:
    out = tpl
    for k, v in mapping.items():
        out = out.replace("{" + k + "}", v)
    return out


def seal_hash(canonical_content_empty_hash: str) -> Tuple[str, str]:
    digest = sha256_hex(canonical_content_empty_hash)
    sealed = canonical_content_empty_hash.replace('value: ""', f'value: "{digest}"', 1)
    return digest, sealed


def append_index_row(index_path: str, row: Dict[str, str]) -> None:
    header = [
        "event_id",
        "date",
        "event_type",
        "title_20",
        "summary_100",
        "importance",
        "canonical_path",
        "content_hash",
        "status",
    ]
    first = read_index_header(index_path)
    if first != ",".join(header):
        die("index csv header mismatch; expected fixed schema")

    with open(index_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header, lineterminator="\n")
        writer.writerow(row)


def run_git(args: List[str]) -> None:
    r = subprocess.run(["git"] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout)
        sys.stderr.write(r.stderr)
        die("git command failed")


def read_optional_file(path: Optional[str]) -> str:
    if not path:
        return ""
    if not os.path.exists(path):
        die(f"file not found: {path}")
    return read_text(path)


def main() -> None:
    ap = argparse.ArgumentParser(description="Create a Decision Unit record (Index + Canonical).")
    ap.add_argument("--title", required=True, help="short title (<=20 chars for index)")
    ap.add_argument("--summary", required=True, help="short summary (<=100 chars for index)")
    ap.add_argument(
        "--event-type",
        required=True,
        choices=[
            "POLICY_CHANGE",
            "ARCH_DECISION",
            "EXTERNAL_DEP",
            "PARADIGM_SHIFT",
            "INCIDENT_RESOLUTION",
            "META_GOV",
        ],
    )
    ap.add_argument("--importance", required=True, choices=["A", "B", "C"])
    ap.add_argument("--date", default=today_iso(), help="YYYY-MM-DD (default: today)")
    ap.add_argument("--status", default="Active", choices=["Draft", "Active", "Deprecated"])
    ap.add_argument("--index", default=os.path.join("governance", "history_index.csv"))
    ap.add_argument("--template", default=os.path.join("governance", "templates", "record_template.md"))
    ap.add_argument("--git", action="store_true", help="git add and commit created/updated files")
    ap.add_argument("--git-message", default="", help="optional commit message override")

    ap.add_argument("--context", default="")
    ap.add_argument("--options", default="")
    ap.add_argument("--decision", default="")
    ap.add_argument("--rationale", default="")
    ap.add_argument("--impact", default="")
    ap.add_argument("--implementation", default="")
    ap.add_argument("--revalidation", default="")

    ap.add_argument("--context-file", default="")
    ap.add_argument("--options-file", default="")
    ap.add_argument("--decision-file", default="")
    ap.add_argument("--rationale-file", default="")
    ap.add_argument("--impact-file", default="")
    ap.add_argument("--implementation-file", default="")
    ap.add_argument("--revalidation-file", default="")
    ns = ap.parse_args()

    date_iso = parse_date(ns.date)
    title_20 = ensure_len("title", ns.title, 20)
    summary_100 = ensure_len("summary", ns.summary, 100)

    index_rows = load_index_rows(ns.index)
    year = dt.date.fromisoformat(date_iso).year
    event_id, seq = next_event_id(index_rows, year)
    canonical_rel = canonical_path_for(date_iso, seq)

    if not os.path.exists(ns.template):
        die(f"template not found: {ns.template}")
    tpl = read_text(ns.template)

    context = ns.context if ns.context else read_optional_file(ns.context_file)
    options = ns.options if ns.options else read_optional_file(ns.options_file)
    decision = ns.decision if ns.decision else read_optional_file(ns.decision_file)
    rationale = ns.rationale if ns.rationale else read_optional_file(ns.rationale_file)
    impact = ns.impact if ns.impact else read_optional_file(ns.impact_file)
    implementation = ns.implementation if ns.implementation else read_optional_file(ns.implementation_file)
    revalidation = ns.revalidation if ns.revalidation else read_optional_file(ns.revalidation_file)

    mapping = {
        "event_id": event_id,
        "date": date_iso,
        "event_type": ns.event_type,
        "importance": ns.importance,
        "status": ns.status,
        "title": ns.title.replace('"', "'"),
        "summary": ns.summary.replace('"', "'"),
        "context": context.rstrip(),
        "options": options.rstrip(),
        "decision": decision.rstrip(),
        "rationale": rationale.rstrip(),
        "impact": impact.rstrip(),
        "implementation": implementation.rstrip(),
        "revalidation": revalidation.rstrip(),
    }

    canonical_empty_hash = fill_template(tpl, mapping)
    digest, canonical_sealed = seal_hash(canonical_empty_hash)

    write_text(canonical_rel, canonical_sealed)

    row = {
        "event_id": event_id,
        "date": date_iso,
        "event_type": ns.event_type,
        "title_20": title_20,
        "summary_100": summary_100,
        "importance": ns.importance,
        "canonical_path": canonical_rel.replace("\\", "/"),
        "content_hash": "sha256:" + digest,
        "status": ns.status,
    }
    append_index_row(ns.index, row)

    if ns.git:
        run_git(["add", ns.index, canonical_rel, ns.template])
        msg = ns.git_message.strip() or f"record {event_id} {ns.event_type}"
        run_git(["commit", "-m", msg])

    sys.stdout.write(f"OK event_id={event_id}\n")
    sys.stdout.write(f"canonical={canonical_rel}\n")
    sys.stdout.write(f"hash=sha256:{digest}\n")


if __name__ == "__main__":
    main()
