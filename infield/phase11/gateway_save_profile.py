import os, json, csv, hashlib, sqlite3, argparse, time
from datetime import datetime, timezone

BASE = r"C:\Users\sirok\MoCKA"
PHASE11 = os.path.join(BASE, "infield", "phase11")
OUTBOX  = os.path.join(BASE, "outbox")
RAW_PATH = os.path.join(PHASE11, "raw_events.jsonl")
CSV_PATH = os.path.join(PHASE11, "structured.csv")
DB_PATH  = os.path.join(PHASE11, "knowledge.db")
HEADER = ["id","timestamp","source","category","summary","raw_text","tags","hash"]

def sha256_text(t): return hashlib.sha256(t.encode("utf-8")).hexdigest()
def sha256_bytes(b):
    h=hashlib.sha256(); h.update(b); return h.hexdigest()

def connect_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=NORMAL;")
    cur.execute("PRAGMA temp_store=MEMORY;")
    return con

def ensure_structured_header():
    if not os.path.isfile(CSV_PATH):
        with open(CSV_PATH, "w", encoding="ascii", newline="") as f:
            csv.writer(f).writerow(HEADER)

def main(source, category, summary, raw_text, tags):
    t0 = time.perf_counter()
    ts = datetime.now(timezone.utc).isoformat()
    content_hash = sha256_text(raw_text)
    record_id = sha256_text("|".join([content_hash, source, category, tags]))
    event = dict(id=record_id,timestamp=ts,source=source,category=category,summary=summary,raw_text=raw_text,tags=tags,hash=content_hash)

    # raw
    a0 = time.perf_counter()
    os.makedirs(os.path.dirname(RAW_PATH), exist_ok=True)
    with open(RAW_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\\n")
    a1 = time.perf_counter()

    # csv
    b0 = time.perf_counter()
    ensure_structured_header()
    with open(CSV_PATH, "a", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow([event[k] for k in HEADER])
    b1 = time.perf_counter()

    # sqlite
    c0 = time.perf_counter()
    con = connect_db()
    cur = con.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO events (id,timestamp,source,category,summary,raw_text,tags,hash) VALUES (?,?,?,?,?,?,?,?)",
        (record_id, ts, source, category, summary, raw_text, tags, content_hash)
    )
    con.commit()
    con.close()
    c1 = time.perf_counter()

    # payload + proof (no reread)
    d0 = time.perf_counter()
    os.makedirs(OUTBOX, exist_ok=True)
    payload_bytes = json.dumps(event, ensure_ascii=False, indent=2).encode("utf-8")
    payload_sha = sha256_bytes(payload_bytes)
    payload_path = os.path.join(OUTBOX, f"{record_id}_payload.json")
    with open(payload_path, "wb") as f:
        f.write(payload_bytes)

    proof = dict(kind="save", id=record_id, timestamp=ts, payload_sha256=payload_sha, payload_file=os.path.basename(payload_path), xlsx_file=None, xlsx_sha256=None)
    proof_path = os.path.join(OUTBOX, f"{record_id}_integrity_proof.json")
    with open(proof_path, "w", encoding="utf-8") as f:
        json.dump(proof, f, ensure_ascii=False, indent=2)
    d1 = time.perf_counter()

    t1 = time.perf_counter()
    print("SAVE_PROFILE_OK", record_id)
    print("t_raw", round(a1-a0,4), "t_csv", round(b1-b0,4), "t_sqlite", round(c1-c0,4), "t_payload_proof", round(d1-d0,4), "t_total", round(t1-t0,4))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="work")
    ap.add_argument("--category", default="memo")
    ap.add_argument("--summary", default="bulk")
    ap.add_argument("--raw_text", default="bulk ingest")
    ap.add_argument("--tags", default="tag1")
    a = ap.parse_args()
    main(a.source,a.category,a.summary,a.raw_text,a.tags)
