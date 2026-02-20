import sqlite3

DB = r"C:\Users\sirok\MoCKA\infield\state\mocka_state.db"

con = sqlite3.connect(DB)
cur = con.cursor()

cur.execute("""
UPDATE retry_queue
SET next_retry_at = strftime('%Y-%m-%d %H:%M:%S', datetime(replace(next_retry_at,'T',' '))),
    last_status_updated_at = strftime('%Y-%m-%d %H:%M:%S', datetime(replace(last_status_updated_at,'T',' ')))
WHERE next_retry_at LIKE '%T%' OR last_status_updated_at LIKE '%T%'
""")
n = cur.rowcount
con.commit()
con.close()

print("Fixed rows =", n)
