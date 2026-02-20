import sqlite3
import datetime

DB  = r"C:\Users\sirok\MoCKA\infield\state\mocka_state.db"
RID = r"R-LOCKTEST-2026-02-17T00:43:59"

con = sqlite3.connect(DB)
cur = con.cursor()

now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

cur.execute(
    "UPDATE retry_queue SET next_retry_at=?, status='queued', last_status_updated_at=? WHERE replan_request_id=?",
    (now, now, RID),
)

con.commit()
con.close()

print("UPDATED next_retry_at =", now)
