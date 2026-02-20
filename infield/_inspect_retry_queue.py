import sqlite3

DB = r"C:\Users\sirok\MoCKA\infield\state\mocka_state.db"

con = sqlite3.connect(DB)
cur = con.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='retry_queue'")
print("retry_queue:", "found" if cur.fetchone() else "not found")

cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='retry_queue'")
row = cur.fetchone()
print("create_sql:")
print(row[0] if row and row[0] else "no sql")

print("columns:")
cur.execute("PRAGMA table_info(retry_queue)")
rows = cur.fetchall()
if not rows:
    print("no columns")
else:
    for r in rows:
        # r = (cid, name, type, notnull, dflt_value, pk)
        print(f"{r[1]} {r[2]} notnull={r[3]} default={r[4]} pk={r[5]}")

con.close()
