import sqlite3
import sys

if len(sys.argv) != 3:
    print("Usage: python show_table_info.py <db_path> <table>")
    sys.exit(1)

db_path = sys.argv[1]
table = sys.argv[2]

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table,))
if cur.fetchone() is None:
    print("DB:", db_path)
    print("TABLE NOT FOUND:", table)
    conn.close()
    sys.exit(2)

cur.execute(f"PRAGMA table_info({table});")
rows = cur.fetchall()

print("DB:", db_path)
print("TABLE:", table)
for r in rows:
    # cid, name, type, notnull, dflt_value, pk
    print(f"- {r[1]} | {r[2]} | notnull={r[3]} | default={r[4]} | pk={r[5]}")

conn.close()