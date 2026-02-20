import sqlite3

DB = r"C:\Users\sirok\MoCKA\infield\state\mocka_state.infield.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;").fetchall()]
print("DB:", DB)
print("TABLES:")
for t in tables:
    print(" -", t)

print("\nCOLUMNS:")
for t in tables:
    cols = cur.execute(f"PRAGMA table_info({t});").fetchall()
    print("\n==", t, "==")
    for c in cols:
        # c = (cid, name, type, notnull, dflt_value, pk)
        print(f"{c[1]} {c[2]}")
conn.close()
