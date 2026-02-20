import os, sys, sqlite3

root = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\sirok\MoCKA"

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

def fix_one_db(dbpath):
  con = sqlite3.connect(dbpath)
  cur = con.cursor()

  if not table_exists(cur, "breaker_state"):
    cols = ",".join([c + " " + t for (c,t) in NEEDED])
    cur.execute("CREATE TABLE breaker_state (" + cols + ")")
    con.commit()
    print("CREATED breaker_state:", dbpath)

  cols = set(existing_cols(cur, "breaker_state"))
  for (c,t) in NEEDED:
    if c not in cols:
      cur.execute("ALTER TABLE breaker_state ADD COLUMN " + c + " " + t)
      print("ADDED column", c, ":", dbpath)

  con.commit()

  cur.execute("PRAGMA table_info(breaker_state)")
  rows = cur.fetchall()
  con.close()

  names = [r[1] for r in rows]
  ok = ("last_error_class" in names)
  print("VERIFY breaker_state columns:", ("OK" if ok else "NG"), dbpath)
  for r in rows:
    print("  ", r)

def find_dbs(rootdir):
  hits = []
  for dp, dn, fn in os.walk(rootdir):
    for f in fn:
      fl = f.lower()
      if fl.startswith("mocka_state") and fl.endswith(".db"):
        hits.append(os.path.join(dp, f))
  return sorted(set(hits))

dbs = find_dbs(root)
print("SCAN ROOT:", root)
print("FOUND DB COUNT:", len(dbs))
for d in dbs:
  print("FOUND:", d)

if not dbs:
  raise SystemExit("No mocka_state*.db found under root")

fail = 0
for db in dbs:
  try:
    fix_one_db(db)
  except Exception as e:
    fail += 1
    print("FAIL:", db, str(e))

if fail:
  raise SystemExit("Some DBs failed: " + str(fail))

print("DONE: all DBs fixed")
