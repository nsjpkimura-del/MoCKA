import sqlite3
import sys

if len(sys.argv) != 2:
    print("Usage: python list_tables.py <db_path>")
    sys.exit(1)

db_path = sys.argv[1]

try:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")

    print("DB:", db_path)
    rows = cur.fetchall()
    if not rows:
        print("(no tables found)")
    else:
        for row in rows:
            print("-", row[0])

    conn.close()

except Exception as e:
    print("ERROR:", e)