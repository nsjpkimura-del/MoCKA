import sqlite3
import datetime

DB = r"C:\Users\sirok\MoCKA\infield\state\mocka_state.db"

con = sqlite3.connect(DB)
cur = con.cursor()

rid = "R-STUCK-" + datetime.datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
old = (datetime.datetime.utcnow() - datetime.timedelta(seconds=3600)).strftime("%Y-%m-%d %H:%M:%S")
now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

cur.execute(
    "INSERT OR REPLACE INTO retry_queue (replan_request_id,event_id,plan_rev,provider_name,error_class,retry_count,max_retry,next_retry_at,status,last_status_updated_at) "
    "VALUES (?,?,?,?,?,?,?,?,?,?)",
    (rid, "E-STUCK", 1, "openai", None, 0, 3, now, "processing", old),
)

con.commit()
con.close()

print(rid)
