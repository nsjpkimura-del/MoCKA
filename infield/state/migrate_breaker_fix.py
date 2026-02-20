import sqlite3

db = r"C:\Users\sirok\MoCKA\infield\state\mocka_state.infield.db"
con = sqlite3.connect(db)
cur = con.cursor()

def col_exists(table, col):
    cur.execute("PRAGMA table_info(" + table + ")")
    for r in cur.fetchall():
        if r[1] == col:
            return True
    return False

cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='breaker_state'")
if not cur.fetchone():
    raise SystemExit("breaker_state table missing")

if not col_exists("breaker_state", "last_error_class"):
    cur.execute("ALTER TABLE breaker_state ADD COLUMN last_error_class TEXT")
    print("MIGRATED: added last_error_class")
else:
    print("OK: column already exists")

con.commit()
con.close()
