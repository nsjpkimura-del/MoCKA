import sqlite3, datetime

db = r'C:\Users\sirok\MoCKA\infield\state\mocka_state.db'
con = sqlite3.connect(db)
cur = con.cursor()

rows = cur.execute("""
SELECT replan_request_id, retry_count, status, next_retry_at
FROM retry_queue
ORDER BY last_status_updated_at DESC
LIMIT 5
""").fetchall()

print("NOW UTC =", datetime.datetime.utcnow().isoformat())
for r in rows:
    print(r)

con.close()
