import sqlite3
import hashlib
import json
import datetime

db = "audit.db"
conn = sqlite3.connect(db)
cur = conn.cursor()

now = datetime.datetime.utcnow().isoformat()

payload = {
    "key_id": "ed25519_20260220_01",
    "action": "activate",
    "policy_version": "1.0",
    "timestamp": now
}

content = json.dumps(payload, sort_keys=True)
event_id = hashlib.sha256(content.encode()).hexdigest()

cur.execute("SELECT chain_hash FROM audit_ledger_event ORDER BY id DESC LIMIT 1")
row = cur.fetchone()
prev_hash = row[0] if row else "GENESIS"

chain_hash = hashlib.sha256((prev_hash + event_id).encode()).hexdigest()

cur.execute("""
INSERT INTO audit_ledger_event
(event_type, schema_version, event_content, event_id, prev_chain_hash, chain_hash, created_at_utc)
VALUES (?, ?, ?, ?, ?, ?, ?)
""", ("key_policy", "v1", content, event_id, prev_hash, chain_hash, now))

conn.commit()
conn.close()

print("Key policy activated:", event_id)