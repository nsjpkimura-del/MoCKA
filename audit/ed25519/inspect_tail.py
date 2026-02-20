import sqlite3

db="audit.db"
conn=sqlite3.connect(db)
cur=conn.cursor()

cur.execute("PRAGMA table_info(audit_ledger_event)")
print("COLUMNS:", [r[1] for r in cur.fetchall()])

cur.execute("SELECT id,event_type,schema_version,event_id,prev_chain_hash,chain_hash,created_at_utc FROM audit_ledger_event ORDER BY id DESC LIMIT 10")
rows=cur.fetchall()
for r in rows:
    print(r)

conn.close()