import sqlite3

db="audit.db"
conn=sqlite3.connect(db)
cur=conn.cursor()

cur.execute("SELECT id,event_type,event_id FROM audit_ledger_event ORDER BY id DESC LIMIT 1")
row=cur.fetchone()
if not row:
    raise SystemExit("no rows")

rid, etype, eid = row
print("LAST:", row)

if etype != "key_policy":
    raise SystemExit("last row is not key_policy; stop")

cur.execute("DELETE FROM audit_ledger_event WHERE id=?", (rid,))
conn.commit()
conn.close()

print("DELETED id=", rid, "event_id=", eid)