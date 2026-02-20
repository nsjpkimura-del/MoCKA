import sqlite3

db = r'C:\Users\sirok\MoCKA\infield\state\mocka_state.db'
con = sqlite3.connect(db)
cur = con.cursor()

rows = cur.execute("""
SELECT replan_request_id, '[' || status || ']', length(status)
FROM retry_queue
""").fetchall()

print("ALL ROWS WITH STATUS:")
for r in rows:
    print(r)

con.close()
