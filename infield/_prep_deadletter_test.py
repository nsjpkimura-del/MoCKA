import os, sqlite3, datetime
db=os.environ["MOCKA_DB"]
con=sqlite3.connect(db)
cur=con.cursor()

rid="R-LOCKTEST-2026-02-17_010312"
due=(datetime.datetime.utcnow()-datetime.timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")

cur.execute("UPDATE retry_queue SET status='queued', retry_count=0, max_retry=1, next_retry_at=?, last_status_updated_at=? WHERE replan_request_id=?", (due, due, rid))
con.commit()

cur.execute("SELECT replan_request_id, status, retry_count, max_retry, next_retry_at FROM retry_queue WHERE replan_request_id=?", (rid,))
print("DEADLETTER_TEST_ROW:", cur.fetchone())
con.close()
