import sqlite3
import hashlib
import json
import datetime
import os
import sys

DB_PATH = "audit.db"
TABLE = "audit_ledger_event"

TARGET_EVENT_TYPE = "key_policy"
TARGET_SCHEMA_VERSION = "v1"

KEY_ID = "ed25519_20260220_01"
POLICY_VERSION = "1.0"
ACTION = "activate"


def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def iso_utc_now() -> str:
    # timezone-aware UTC (avoids utcnow deprecation)
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def looks_json(s: str) -> bool:
    s2 = (s or "").strip()
    return s2.startswith("{") and s2.endswith("}")


def canonicalize_json_str(s: str, separators, sort_keys: bool) -> str:
    obj = json.loads(s)
    return json.dumps(obj, ensure_ascii=False, sort_keys=sort_keys, separators=separators)


def generate_candidate_event_id_inputs(event_type: str, schema_version: str, event_content: str):
    ec_raw = event_content if event_content is not None else ""
    ec_strip = ec_raw.strip()

    yield ("ec_raw", ec_raw.encode("utf-8"))
    yield ("ec_strip", ec_strip.encode("utf-8"))

    join_variants = [
        ("pipe", "|"),
        ("nl", "\n"),
        ("empty", ""),
    ]

    parts = [
        ("etype|sv|ec", (event_type, schema_version, ec_raw)),
        ("etype|ec", (event_type, ec_raw)),
        ("sv|ec", (schema_version, ec_raw)),
        ("etype|sv|ec_strip", (event_type, schema_version, ec_strip)),
        ("etype|ec_strip", (event_type, ec_strip)),
        ("sv|ec_strip", (schema_version, ec_strip)),
    ]

    for jname, sep in join_variants:
        for pname, p in parts:
            yield (f"{pname}__{jname}", sep.join(p).encode("utf-8"))

    if looks_json(ec_raw):
        json_variants = []
        try:
            json_variants.append(("json_sort_nospace", canonicalize_json_str(ec_raw, separators=(",", ":"), sort_keys=True)))
        except Exception:
            pass
        try:
            json_variants.append(("json_sort_space", canonicalize_json_str(ec_raw, separators=(", ", ": "), sort_keys=True)))
        except Exception:
            pass
        try:
            obj = json.loads(ec_raw)
            json_variants.append(("json_nosort_nospace", json.dumps(obj, ensure_ascii=False, sort_keys=False, separators=(",", ":"))))
        except Exception:
            pass

        for vname, jstr in json_variants:
            yield (vname, jstr.encode("utf-8"))
            yield (vname + "_strip", jstr.strip().encode("utf-8"))
            for jname, sep in join_variants:
                yield (f"etype|sv|{vname}__{jname}", sep.join([event_type, schema_version, jstr]).encode("utf-8"))
                yield (f"etype|{vname}__{jname}", sep.join([event_type, jstr]).encode("utf-8"))
                yield (f"sv|{vname}__{jname}", sep.join([schema_version, jstr]).encode("utf-8"))


def infer_event_id_rule(rows):
    per_row_matches = []
    for r in rows:
        etype = r["event_type"]
        sv = r["schema_version"]
        ec = r["event_content"]
        eid = r["event_id"]

        matches = set()
        for name, b in generate_candidate_event_id_inputs(etype, sv, ec):
            if sha256_hex(b) == eid:
                matches.add(name)
        per_row_matches.append(matches)

    common = set.intersection(*per_row_matches) if per_row_matches else set()
    if not common:
        return None, None, per_row_matches

    preference = [
        "ec_raw",
        "ec_strip",
        "etype|sv|ec__pipe",
        "etype|sv|ec__empty",
        "etype|sv|ec_strip__pipe",
        "json_sort_nospace",
        "etype|sv|json_sort_nospace__pipe",
        "json_sort_space",
        "etype|sv|json_sort_space__pipe",
        "json_nosort_nospace",
        "etype|sv|json_nosort_nospace__pipe",
    ]
    chosen = None
    for p in preference:
        if p in common:
            chosen = p
            break
    if chosen is None:
        chosen = sorted(common)[0]

    def compute_event_id(event_type: str, schema_version: str, event_content: str) -> str:
        for name, b in generate_candidate_event_id_inputs(event_type, schema_version, event_content):
            if name == chosen:
                return sha256_hex(b)
        raise RuntimeError("chosen event_id rule not reproducible")

    return compute_event_id, chosen, per_row_matches


def infer_chain_hash_rule(rows):
    # IMPORTANT: ignore rows with NULL prev_chain_hash (genesis-style row)
    rows2 = [r for r in rows if r.get("prev_chain_hash") is not None]

    def candidates(prev_hash: str, eid: str):
        yield ("prev+eid", (prev_hash + eid).encode("utf-8"))
        yield ("prev|eid", (prev_hash + "|" + eid).encode("utf-8"))
        yield ("eid+prev", (eid + prev_hash).encode("utf-8"))
        yield ("eid|prev", (eid + "|" + prev_hash).encode("utf-8"))

    per_row_matches = []
    for r in rows2:
        prevh = r["prev_chain_hash"]
        eid = r["event_id"]
        ch = r["chain_hash"]
        if prevh is None or eid is None or ch is None:
            continue

        matches = set()
        for name, b in candidates(prevh, eid):
            if sha256_hex(b) == ch:
                matches.add(name)
        per_row_matches.append(matches)

    common = set.intersection(*per_row_matches) if per_row_matches else set()
    if not common:
        return None, None, per_row_matches

    preference = ["prev+eid", "prev|eid", "eid+prev", "eid|prev"]
    chosen = next((p for p in preference if p in common), sorted(common)[0])

    def compute_chain_hash(prev_hash: str, eid: str) -> str:
        for name, b in candidates(prev_hash, eid):
            if name == chosen:
                return sha256_hex(b)
        raise RuntimeError("chosen chain_hash rule not reproducible")

    return compute_chain_hash, chosen, per_row_matches


def table_columns(cur):
    cur.execute(f"PRAGMA table_info({TABLE})")
    return [r[1] for r in cur.fetchall()]


def fetch_all_rows(cur):
    cur.execute(f"SELECT id,event_type,schema_version,event_content,event_id,prev_chain_hash,chain_hash,created_at_utc FROM {TABLE} ORDER BY id ASC")
    cols = [d[0] for d in cur.description]
    out = []
    for row in cur.fetchall():
        out.append({cols[i]: row[i] for i in range(len(cols))})
    return out


def main():
    if not os.path.exists(DB_PATH):
        print("ERROR: audit.db not found:", os.path.abspath(DB_PATH))
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cols = table_columns(cur)
    required = ["event_type", "schema_version", "event_content", "event_id", "prev_chain_hash", "chain_hash", "created_at_utc"]
    missing = [c for c in required if c not in cols]
    if missing:
        print("ERROR: missing required columns:", missing)
        print("COLUMNS:", cols)
        sys.exit(1)

    rows = fetch_all_rows(cur)
    if len(rows) < 2:
        print("ERROR: need at least 2 rows in ledger to proceed. rows=", len(rows))
        sys.exit(1)

    event_id_fn, event_rule_name, _ = infer_event_id_rule(rows)
    chain_fn, chain_rule_name, _ = infer_chain_hash_rule(rows)

    if event_id_fn is None:
        print("ERROR: could not infer event_id rule from existing rows.")
        sys.exit(1)

    if chain_fn is None:
        print("ERROR: could not infer chain_hash rule from existing rows (prev_chain_hash might be NULL-only).")
        sys.exit(1)

    print("INFERRED event_id rule:", event_rule_name)
    print("INFERRED chain_hash rule:", chain_rule_name)

    # Idempotency: if a key_policy row already exists for this key_id, skip
    cur.execute(f"SELECT id,event_type,event_content,event_id FROM {TABLE} WHERE event_type=? ORDER BY id DESC LIMIT 1", (TARGET_EVENT_TYPE,))
    last_kp = cur.fetchone()
    if last_kp and isinstance(last_kp[2], str) and KEY_ID in last_kp[2]:
        print("SKIP: key_policy already exists. last=", last_kp)
        conn.close()
        return

    payload = {"action": ACTION, "key_id": KEY_ID, "policy_version": POLICY_VERSION}
    event_content = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    event_id = event_id_fn(TARGET_EVENT_TYPE, TARGET_SCHEMA_VERSION, event_content)

    cur.execute(f"SELECT chain_hash FROM {TABLE} ORDER BY id DESC LIMIT 1")
    prev_hash = cur.fetchone()[0]

    chain_hash = chain_fn(prev_hash, event_id)
    created_at_utc = iso_utc_now()

    cur.execute(
        f"""
        INSERT INTO {TABLE}
        (event_type, schema_version, event_content, event_id, prev_chain_hash, chain_hash, created_at_utc)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (TARGET_EVENT_TYPE, TARGET_SCHEMA_VERSION, event_content, event_id, prev_hash, chain_hash, created_at_utc),
    )

    conn.commit()
    conn.close()

    print("INSERTED key_policy")
    print("  event_id:", event_id)
    print("  created_at_utc:", created_at_utc)


if __name__ == "__main__":
    main()