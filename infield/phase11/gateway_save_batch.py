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

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def connect_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=NORMAL;")
    cur.execute("PRAGMA temp_store=MEMORY;")
    cur.execute("PRAGMA wal_autocheckpoint=1000;")
    cur.execute("PRAGMA busy_timeout=3000;")
    cur.execute("PRAGMA mmap_size=268435456;")
    return con

def ensure_structured_header():
    if not os.path.isfile(CSV_PATH):
        with open(CSV_PATH, "w", encoding="ascii", newline="") as f:
            csv.writer(f).writerow(HEADER)

def make_event(source, category, summary, raw_text, tags):
    ts = datetime.now(timezone.utc).isoformat()
    content_hash = sha256_text(raw_text)
    rid = sha256_text("|".join([content_hash, source, category, tags]))
    return {
        "id": rid,
        "timestamp": ts,
        "source": source,
        "category": category,
        "summary": summary,
        "raw_text": raw_text,
        "tags": tags,
        "hash": content_hash
    }

def main(source, category, summary, tags, n, base_text):
    t0 = time.perf_counter()
    batch_ts = datetime.now(timezone.utc).isoformat()
    batch_id = sha256_text("batch|" + batch_ts + "|" + source + "|" + category + "|" + tags + "|" + str(n))

    os.makedirs(os.path.dirname(RAW_PATH), exist_ok=True)
    os.makedirs(OUTBOX, exist_ok=True)
    ensure_structured_header()

    con = connect_db()
    cur = con.cursor()

    events = []
    for i in range(n):
        raw_text = f"{base_text} #{i} {datetime.now(timezone.utc).isoformat()}"
        events.append(make_event(source, category, summary, raw_text, tags))

    # raw + csv append
    with open(RAW_PATH, "a", encoding="utf-8") as fr, open(CSV_PATH, "a", encoding="utf-8", newline="") as fc:
        w = csv.writer(fc)
        for e in events:
            fr.write(json.dumps(e, ensure_ascii=False) + "\\n")
            w.writerow([e[k] for k in HEADER])

    # sqlite batched insert
    cur.executemany(
        "INSERT OR IGNORE INTO events (id,timestamp,source,category,summary,raw_text,tags,hash) VALUES (?,?,?,?,?,?,?,?)",
        [(e["id"], e["timestamp"], e["source"], e["category"], e["summary"], e["raw_text"], e["tags"], e["hash"]) for e in events]
    )
    con.commit()
    con.close()

    # batch payload + proof
    payload = {
        "kind": "batch_save",
        "batch_id": batch_id,
        "timestamp": batch_ts,
        "n": n,
        "source": source,
        "category": category,
        "tags": tags,
        "ids": [e["id"] for e in events],
    }
    payload_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    payload_sha = sha256_bytes(payload_bytes)

    payload_path = os.path.join(OUTBOX, f"batch_{batch_id}_payload.json")
    with open(payload_path, "wb") as f:
        f.write(payload_bytes)

    proof = {
        "kind": "batch_save",
        "batch_id": batch_id,
        "timestamp": batch_ts,
        "payload_file": os.path.basename(payload_path),
        "payload_sha256": payload_sha,
        "db_file": os.path.basename(DB_PATH),
        "db_sha256": sha256_file(DB_PATH),
    }
    proof_path = os.path.join(OUTBOX, f"batch_{batch_id}_integrity_proof.json")
    with open(proof_path, "w", encoding="utf-8") as f:
        json.dump(proof, f, ensure_ascii=False, indent=2)

    t1 = time.perf_counter()
    print("BATCH_SAVE_OK", "batch_id", batch_id, "n", n, "t_total", round(t1-t0,4), "per_item", round((t1-t0)/n,4))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="work")
    ap.add_argument("--category", default="memo")
    ap.add_argument("--summary", default="bulk")
    ap.add_argument("--tags", default="tag1")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--base_text", default="batch ingest")
    a = ap.parse_args()
    main(a.source,a.category,a.summary,a.tags,a.n,a.base_text)
