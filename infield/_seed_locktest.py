import sqlite3
import datetime

DB = r"C:\Users\sirok\MoCKA\infield\state\mocka_state.db"

con = sqlite3.connect(DB)
cur = con.cursor()

rid = "R-LOCKTEST-" + datetime.datetime.utcnow().replace(microsecond=0).isoformat()
now = datetime.datetime.utcnow().replace(microsecond=0).isoformat()

cur.execute(
    "INSERT OR REPLACE INTO retry_queue (replan_request_id,event_id,plan_rev,provider_name,error_class,retry_count,max_retry,next_retry_at,status,last_status_updated_at) "
    "VALUES (?,?,?,?,?,?,?,?,?,?)",
    (rid, "E-LOCKTEST", 1, "openai", None, 0, 3, now, "queued", now),
)

con.commit()
con.close()

print(rid)
