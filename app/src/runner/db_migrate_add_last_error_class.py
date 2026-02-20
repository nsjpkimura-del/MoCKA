import sqlite3

DBS = [
    r"C:\Users\sirok\MoCKA\infield\state\mocka_state.infield.db",
    r"C:\Users\sirok\MoCKA\infield\state\mocka_state.outfield.db",
]

SQL = "ALTER TABLE provider_breaker ADD COLUMN last_error_class TEXT;"

for path in DBS:
    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute(SQL)
        conn.commit()
        print("OK:", path)
    except Exception as e:
        print("SKIP:", path, repr(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass
