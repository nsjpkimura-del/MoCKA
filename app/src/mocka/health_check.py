# ============================================================
# mocka_health_check.py  (MoCKA 3.0 / 運用監査チェック)
# - SQLite(state) の整合性と詰まりを検知
# - retry_queue の滞留 / running 固着 / next_retry_at 破綻
# - breaker_state の open 固着 / half-open 長期滞留
# - metrics の日次増分を確認
# ============================================================

import os
import sys
import sqlite3
from datetime import datetime, timezone, timedelta

INFIELD_BASE = r"C:\Users\sirok\mocka-infield"
DB_PATH = os.path.join(INFIELD_BASE, "state", "mocka_state.db")

# 監査閾値（必要なら環境変数で上書き可）
RUNNING_STUCK_MIN = int(os.environ.get("MOCKA_AUDIT_RUNNING_STUCK_MIN", "70"))  # running 固着
OPEN_STUCK_MIN = int(os.environ.get("MOCKA_AUDIT_OPEN_STUCK_MIN", "120"))       # open 固着
HALFOPEN_STUCK_MIN = int(os.environ.get("MOCKA_AUDIT_HALFOPEN_STUCK_MIN", "30"))# half-open 固着
QUEUED_BACKLOG_WARN = int(os.environ.get("MOCKA_AUDIT_QUEUED_BACKLOG_WARN", "50"))

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def iso_to_dt(s: str) -> datetime:
    return datetime.fromisoformat(s)

def conn_db() -> sqlite3.Connection:
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(DB_PATH)
    conn = sqlite3.connect(DB_PATH, timeout=15, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn

def q1(conn: sqlite3.Connection, sql: str, params=()):
    cur = conn.cursor()
    return cur.execute(sql, params).fetchone()

def qa(conn: sqlite3.Connection, sql: str, params=()):
    cur = conn.cursor()
    return cur.execute(sql, params).fetchall()

def check_tables(conn: sqlite3.Connection) -> None:
    need = {"retry_queue", "breaker_state", "metrics"}
    rows = qa(conn, "SELECT name FROM sqlite_master WHERE type='table'")
    have = {r["name"] for r in rows}
    missing = need - have
    if missing:
        raise RuntimeError(f"Missing tables: {sorted(missing)}")
    print("[OK] tables exist:", ", ".join(sorted(need)))

def check_retry_queue(conn: sqlite3.Connection) -> int:
    now = utcnow()

    total = q1(conn, "SELECT COUNT(*) AS c FROM retry_queue")["c"]
    queued = q1(conn, "SELECT COUNT(*) AS c FROM retry_queue WHERE status='queued'")["c"]
    running = q1(conn, "SELECT COUNT(*) AS c FROM retry_queue WHERE status='running'")["c"]
    done = q1(conn, "SELECT COUNT(*) AS c FROM retry_queue WHERE status='done'")["c"]
    dead = q1(conn, "SELECT COUNT(*) AS c FROM retry_queue WHERE status='deadletter'")["c"]

    print(f"[INFO] retry_queue totals: total={total} queued={queued} running={running} done={done} deadletter={dead}")

    rc = 0

    # queued バックログ警告
    if queued >= QUEUED_BACKLOG_WARN:
        print(f"[WARN] queued backlog high: {queued} (>= {QUEUED_BACKLOG_WARN})")
        rc = max(rc, 1)
    else:
        print("[OK] queued backlog level")

    # 実行期限が過去なのに queued のまま
    overdue = q1(conn, """
        SELECT COUNT(*) AS c
        FROM retry_queue
        WHERE status='queued' AND next_retry_at <= ?
    """, (now.isoformat(),))["c"]

    if overdue > 0:
        print(f"[WARN] overdue queued items: {overdue} (next_retry_at <= now)")
        rc = max(rc, 1)
    else:
        print("[OK] no overdue queued items")

    # running 固着
    cutoff = (now - timedelta(minutes=RUNNING_STUCK_MIN)).isoformat()
    stuck_running = q1(conn, """
        SELECT COUNT(*) AS c
        FROM retry_queue
        WHERE status='running' AND last_status_updated_at < ?
    """, (cutoff,))["c"]

    if stuck_running > 0:
        print(f"[ERROR] stuck running items: {stuck_running} (older than {RUNNING_STUCK_MIN} min)")
        rc = max(rc, 2)
        samples = qa(conn, """
            SELECT replan_request_id, event_id, provider_name, last_status_updated_at
            FROM retry_queue
            WHERE status='running' AND last_status_updated_at < ?
            ORDER BY last_status_updated_at
            LIMIT 5
        """, (cutoff,))
        for s in samples:
            print("  [SAMPLE] ", dict(s))
    else:
        print("[OK] no stuck running items")

    # next_retry_at の ISO 破綻（fromisoformat に失敗する値が入っていないか）
    # SQLite上で厳密検証しにくいので、怪しい形式だけ検知（長さ/NULL）
    bad_ts = q1(conn, """
        SELECT COUNT(*) AS c
        FROM retry_queue
        WHERE next_retry_at IS NULL OR length(next_retry_at) < 10
    """)["c"]
    if bad_ts > 0:
        print(f"[WARN] suspicious next_retry_at values: {bad_ts}")
        rc = max(rc, 1)
    else:
        print("[OK] next_retry_at looks sane")

    return rc

def check_breaker(conn: sqlite3.Connection) -> int:
    now = utcnow()
    rc = 0

    rows = qa(conn, "SELECT provider_name, state, opened_at, next_retry_at, recent_error_count, last_error_ts FROM breaker_state")
    if not rows:
        print("[INFO] breaker_state is empty (providers not yet recorded)")
        return 0

    print("[INFO] breaker_state rows:", len(rows))

    for r in rows:
        provider = r["provider_name"]
        state = r["state"]
        opened_at = r["opened_at"]
        next_retry_at = r["next_retry_at"]

        if state == "open":
            if opened_at:
                try:
                    opened = iso_to_dt(opened_at)
                    mins = int((now - opened).total_seconds() / 60)
                    if mins >= OPEN_STUCK_MIN:
                        print(f"[WARN] breaker open too long: provider={provider} open_mins={mins} (>= {OPEN_STUCK_MIN})")
                        rc = max(rc, 1)
                    else:
                        print(f"[OK] breaker open: provider={provider} open_mins={mins}")
                except Exception:
                    print(f"[WARN] breaker opened_at parse error: provider={provider} opened_at={opened_at}")
                    rc = max(rc, 1)
            else:
                print(f"[WARN] breaker open but opened_at is NULL: provider={provider}")
                rc = max(rc, 1)

            if next_retry_at:
                try:
                    nra = iso_to_dt(next_retry_at)
                    if nra <= now:
                        print(f"[WARN] breaker open but next_retry_at already passed: provider={provider} next_retry_at={next_retry_at}")
                        rc = max(rc, 1)
                except Exception:
                    print(f"[WARN] breaker next_retry_at parse error: provider={provider} next_retry_at={next_retry_at}")
                    rc = max(rc, 1)

        elif state == "half-open":
            # half-open の長期滞留は「試行が行われていない」兆候
            if opened_at:
                try:
                    opened = iso_to_dt(opened_at)
                    mins = int((now - opened).total_seconds() / 60)
                    if mins >= HALFOPEN_STUCK_MIN:
                        print(f"[WARN] breaker half-open too long: provider={provider} halfopen_mins={mins} (>= {HALFOPEN_STUCK_MIN})")
                        rc = max(rc, 1)
                    else:
                        print(f"[OK] breaker half-open: provider={provider} halfopen_mins={mins}")
                except Exception:
                    print(f"[WARN] breaker opened_at parse error: provider={provider} opened_at={opened_at}")
                    rc = max(rc, 1)
            else:
                # half-open なのに opened_at がないのは実装方針によっては許容だが一応警告
                print(f"[WARN] breaker half-open with opened_at NULL: provider={provider}")
                rc = max(rc, 1)

        elif state == "closed":
            print(f"[OK] breaker closed: provider={provider}")
        else:
            print(f"[ERROR] breaker invalid state: provider={provider} state={state}")
            rc = max(rc, 2)

    return rc

def check_metrics(conn: sqlite3.Connection) -> int:
    rc = 0
    d = utcnow().strftime("%Y-%m-%d")

    rows = qa(conn, """
        SELECT provider_name, status, error_class, count
        FROM metrics
        WHERE date=?
        ORDER BY provider_name, status, error_class
    """, (d,))

    if not rows:
        print(f"[WARN] no metrics for today: {d}")
        return 1

    print(f"[INFO] metrics for {d}:")
    for r in rows:
        provider = r["provider_name"]
        status = r["status"]
        error_class = r["error_class"]
        count = r["count"]
        print(f"  {provider}  {status}  {error_class}  {count}")

    return rc

def main() -> int:
    conn = conn_db()
    try:
        check_tables(conn)
        rc1 = check_retry_queue(conn)
        rc2 = check_breaker(conn)
        rc3 = check_metrics(conn)
        rc = max(rc1, rc2, rc3)
        if rc == 0:
            print("[PASS] MoCKA state looks healthy")
        elif rc == 1:
            print("[WARN] MoCKA state has warnings")
        else:
            print("[FAIL] MoCKA state has errors")
        return rc
    finally:
        conn.close()

if __name__ == "__main__":
    raise SystemExit(main())
