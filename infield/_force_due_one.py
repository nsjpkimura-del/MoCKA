import os, sqlite3, datetime

db = os.environ.get("MOCKA_DB", r"C:\Users\sirok\MoCKA\infield\state\mocka_state.db")
con = sqlite3.connect(db)
cur = con.cursor()

cur.execute("SELECT replan_request_id FROM retry_queue WHERE replan_request_id LIKE 'R-LOCKTEST-%' ORDER BY last_status_updated_at DESC LIMIT 1")
r = cur.fetchone()
if not r:
    cur.execute("SELECT replan_request_id FROM retry_queue ORDER BY last_status_updated_at DESC LIMIT 1")
    r = cur.fetchone()

if not r:
    print("NO ROWS IN retry_queue")
    raise SystemExit(1)

rid = r[0]
due = (datetime.datetime.utcnow() - datetime.timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")

cur.execute(
    "UPDATE retry_queue SET status='queued', next_retry_at=?, last_status_updated_at=? WHERE replan_request_id=?",
    (due, due, rid)
)
con.commit()

cur.execute("SELECT replan_request_id, status, retry_count, next_retry_at FROM retry_queue WHERE replan_request_id=?", (rid,))
print("FORCED_DUE_ROW:", cur.fetchone())

cur.execute("SELECT COUNT(*) FROM retry_queue WHERE status='queued' AND next_retry_at <= ?", (due,))
print("DUE_QUEUED_COUNT_AT_DUE:", cur.fetchone()[0])

con.close()
