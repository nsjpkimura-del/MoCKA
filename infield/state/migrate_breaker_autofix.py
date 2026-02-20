import sqlite3

db = r"C:\Users\sirok\MoCKA\infield\state\mocka_state.infield.db"
con = sqlite3.connect(db)
cur = con.cursor()

def table_exists(name):
    cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None

def col_exists(table, col):
    cur.execute("PRAGMA table_info(" + table + ")")
    return any(r[1] == col for r in cur.fetchall())

# Create breaker_state if missing (minimal columns + evolvable)
if not table_exists("breaker_state"):
    cur.execute(
        "CREATE TABLE breaker_state ("
        "provider_name TEXT PRIMARY KEY,"
        "window_start_utc TEXT,"
        "fail_count INTEGER DEFAULT 0,"
        "last_error_class TEXT"
        ")"
    )
    print("CREATED: breaker_state")
else:
    print("OK: breaker_state exists")

# Ensure column last_error_class
if not col_exists("breaker_state", "last_error_class"):
    cur.execute("ALTER TABLE breaker_state ADD COLUMN last_error_class TEXT")
    print("MIGRATED: added last_error_class")
else:
    print("OK: last_error_class exists")

con.commit()
con.close()
