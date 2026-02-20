import os
import sqlite3

INFIELD_BASE = r"C:\Users\sirok\mocka-infield"
DB_PATH = os.path.join(INFIELD_BASE, "state", "mocka_state.db")

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print("breaker_state:")
    for r in cur.execute("SELECT * FROM breaker_state").fetchall():
        print(dict(r))

    print("\nretry_queue:")
    for r in cur.execute("SELECT * FROM retry_queue ORDER BY next_retry_at").fetchall():
        print(dict(r))

    print("\nmetrics(today):")
    # 今日の行が無いか、そもそも metrics 全体が空かを確認
    rows_all = cur.execute("SELECT COUNT(*) AS c FROM metrics").fetchone()["c"]
    print("metrics_total_rows:", rows_all)

    from datetime import datetime, timezone
    d = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for r in cur.execute("SELECT * FROM metrics WHERE date=? ORDER BY provider_name,status,error_class", (d,)).fetchall():
        print(dict(r))

    conn.close()

if __name__ == "__main__":
    main()
