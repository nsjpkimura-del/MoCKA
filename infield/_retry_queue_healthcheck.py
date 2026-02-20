import sqlite3
import datetime

DB = r"C:\Users\sirok\MoCKA\infield\state\mocka_state.db"
now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
cutoff = (datetime.datetime.utcnow() - datetime.timedelta(seconds=600)).strftime("%Y-%m-%d %H:%M:%S")

con = sqlite3.connect(DB)
cur = con.cursor()

def one(sql, params=()):
    r = cur.execute(sql, params).fetchone()
    return r[0] if r else 0

print("UTC_NOW =", now)
print("queued_due =", one("SELECT COUNT(*) FROM retry_queue WHERE status='queued' AND next_retry_at <= ?", (now,)))
print("queued_future =", one("SELECT COUNT(*) FROM retry_queue WHERE status='queued' AND next_retry_at > ?", (now,)))
print("processing_total =", one("SELECT COUNT(*) FROM retry_queue WHERE status='processing'"))
print("processing_stale =", one("SELECT COUNT(*) FROM retry_queue WHERE status='processing' AND last_status_updated_at <= ?", (cutoff,)))
print("deadletter =", one("SELECT COUNT(*) FROM retry_queue WHERE status='deadletter'"))
print("done =", one("SELECT COUNT(*) FROM retry_queue WHERE status='done'"))

con.close()
