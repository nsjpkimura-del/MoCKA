import os, sqlite3
db=os.environ["MOCKA_DB"]
con=sqlite3.connect(db)
cur=con.cursor()
rid="R-LOCKTEST-2026-02-17_010312"
cur.execute("SELECT replan_request_id, status, retry_count, max_retry, next_retry_at, error_class FROM retry_queue WHERE replan_request_id=?", (rid,))
print("AFTER_RUN:", cur.fetchone())
con.close()
