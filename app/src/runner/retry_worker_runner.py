import os, sqlite3, datetime
def _dbg_dump(dbpath):
    try:
        con = sqlite3.connect(dbpath)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='breaker_state'")
        t = cur.fetchone()
        cols = []
        if t:
            cur.execute("PRAGMA table_info(breaker_state)")
            cols = [r[1] for r in cur.fetchall()]
        con.close()
        with open(r"C:\Users\sirok\MoCKA\infield\logs\runner_debug.dbpath.log","a",encoding="utf-8") as f:
            f.write("UTC=" + datetime.datetime.utcnow().isoformat() + " DB=" + dbpath + " breaker_state=" + str(bool(t)) + " cols=" + ",".join(cols) + "\n")
    except Exception as e:
        with open(r"C:\Users\sirok\MoCKA\infield\logs\runner_debug.dbpath.log","a",encoding="utf-8") as f:
            f.write("UTC=" + datetime.datetime.utcnow().isoformat() + " DB=" + dbpath + " DBG_FAIL=" + str(e) + "\n")

_dbg_db = os.environ.get("MOCKA_DB","")
if _dbg_db:
    _dbg_dump(_dbg_db)
else:
    with open(r"C:\Users\sirok\MoCKA\infield\logs\runner_debug.dbpath.log","a",encoding="utf-8") as f:
        f.write("UTC=" + datetime.datetime.utcnow().isoformat() + " MOCKA_DB is empty\n")
from mocka.replan_bridge_auto import get_conn, retry_worker_once

if __name__ == '__main__':
    conn = get_conn()
    retry_worker_once(conn)

