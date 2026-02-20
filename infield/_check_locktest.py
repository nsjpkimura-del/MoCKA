import sqlite3
DB  = r"C:\Users\sirok\MoCKA\infield\state\mocka_state.db"
RID = r"R-LOCKTEST-2026-02-17T00:43:59"

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cur = con.cursor()
r = cur.execute(
    "SELECT replan_request_id,status,next_retry_at,last_status_updated_at FROM retry_queue WHERE replan_request_id=?",
    (RID,),
).fetchone()
print(dict(r) if r else "NOT FOUND")
con.close()
