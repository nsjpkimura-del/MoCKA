import sqlite3

DBS = [
  r"",
  r"",
]

NEEDED = [
  ("provider_name","TEXT"),
  ("state","TEXT"),
  ("recent_error_count","INTEGER DEFAULT 0"),
  ("last_error_ts","TEXT"),
  ("last_error_class","TEXT"),
  ("opened_at","TEXT"),
  ("next_retry_at","TEXT"),
]

def table_exists(cur, name):
  cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,))
  return cur.fetchone() is not None

def existing_cols(cur, table):
  cur.execute("PRAGMA table_info(" + table + ")")
  return [r[1] for r in cur.fetchall()]

for db in DBS:
  try:
    con = sqlite3.connect(db)
    cur = con.cursor()

    if not table_exists(cur, "breaker_state"):
      cols = ",".join([c + " " + t for (c,t) in NEEDED])
      cur.execute("CREATE TABLE breaker_state (" + cols + ")")
      con.commit()
      print("CREATED breaker_state in", db)

    cols = set(existing_cols(cur, "breaker_state"))
    for (c,t) in NEEDED:
      if c not in cols:
        cur.execute("ALTER TABLE breaker_state ADD COLUMN " + c + " " + t)
        print("ADDED", c, "to", db)

    con.commit()
    con.close()
    print("OK", db)

  except Exception as e:
    print("FAIL", db, str(e))
