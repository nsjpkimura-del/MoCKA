import sqlite3, datetime

DB = r"C:\Users\sirok\MoCKA\infield\state\mocka_state.db"
con = sqlite3.connect(DB)
cur = con.cursor()

now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

queued_due = cur.execute("SELECT count(*) FROM retry_queue WHERE status='queued' AND next_retry_at <= ?", (now,)).fetchone()[0]
queued_future = cur.execute("SELECT count(*) FROM retry_queue WHERE status='queued' AND next_retry_at > ?", (now,)).fetchone()[0]
processing_total = cur.execute("SELECT count(*) FROM retry_queue WHERE status='processing'").fetchone()[0]
deadletter = cur.execute("SELECT count(*) FROM retry_queue WHERE status='deadletter'").fetchone()[0]
done = cur.execute("SELECT count(*) FROM retry_queue WHERE status='done'").fetchone()[0]

con.close()

print("UTC_NOW =", now)
print("queued_due =", queued_due)
print("queued_future =", queued_future)
print("processing_total =", processing_total)
print("deadletter =", deadletter)
print("done =", done)
