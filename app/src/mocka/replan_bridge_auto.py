import os
import sqlite3
import hashlib
from datetime import datetime, timedelta

FILE_STAMP = hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:12]
WORKER_TAG = os.getenv("WORKER_TAG", "NO_TAG")

DEFAULT_DB = r"C:\Users\sirok\MoCKA\infield\state\mocka_state.db"
DB_PATH = os.getenv("MOCKA_DB", DEFAULT_DB)

# retry間隔（失敗時に何分後へ送るか）
RETRY_DELAY_MINUTES = 5
# stale processing 判定（秒）
STALE_SECONDS = 300


def now_sql():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def get_conn(db_path: str = None):
    p = db_path or DB_PATH
    conn = sqlite3.connect(p, timeout=5.0)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("PRAGMA busy_timeout=5000;")
    cur.execute("PRAGMA foreign_keys=ON;")
    return conn


def recover_stale_processing(conn, stale_seconds: int = STALE_SECONDS):
    cutoff = (datetime.utcnow() - timedelta(seconds=stale_seconds)).strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.cursor()
    cur.execute("PRAGMA busy_timeout=5000;")

    cur.execute(
        """
        UPDATE retry_queue
        SET status='queued'
        WHERE status='processing'
          AND last_status_updated_at < ?
        """,
        (cutoff,),
    )
    recovered = cur.rowcount
    conn.commit()

    if recovered:
        print(f"[WORKER] recovered stale={recovered} tag={WORKER_TAG} stamp={FILE_STAMP}")
    return recovered


def fetch_next_retry(conn):
    cur = conn.cursor()
    cur.execute("PRAGMA busy_timeout=5000;")

    now = now_sql()
    cur.execute(
        """
        UPDATE retry_queue
        SET status='processing',
            last_status_updated_at=?
        WHERE replan_request_id = (
            SELECT replan_request_id
            FROM retry_queue
            WHERE status='queued'
              AND next_retry_at <= ?
            ORDER BY next_retry_at ASC
            LIMIT 1
        )
        RETURNING *
        """,
        (now, now),
    )
    row = cur.fetchone()
    conn.commit()

    if row is not None:
        rid = row["replan_request_id"]
        print(f"[WORKER] fetched id={rid} tag={WORKER_TAG} stamp={FILE_STAMP}")
    return row


def _mark_done(conn, rid: str):
    cur = conn.cursor()
    cur.execute("PRAGMA busy_timeout=5000;")
    cur.execute(
        """
        UPDATE retry_queue
        SET status='done',
            last_status_updated_at=?
        WHERE replan_request_id=?
        """,
        (now_sql(), rid),
    )
    conn.commit()


def _mark_deadletter(conn, rid: str, reason: str):
    cur = conn.cursor()
    cur.execute("PRAGMA busy_timeout=5000;")
    cur.execute(
        """
        UPDATE retry_queue
        SET status='deadletter',
            error_class=?,
            last_status_updated_at=?
        WHERE replan_request_id=?
        """,
        (reason, now_sql(), rid),
    )
    conn.commit()


def _mark_retry_scheduled(conn, rid: str):
    cur = conn.cursor()
    cur.execute("PRAGMA busy_timeout=5000;")

    next_retry = (datetime.utcnow() + timedelta(minutes=RETRY_DELAY_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")
    cur.execute(
        """
        UPDATE retry_queue
        SET status='queued',
            retry_count=retry_count+1,
            next_retry_at=?,
            last_status_updated_at=?
        WHERE replan_request_id=?
        """,
        (next_retry, now_sql(), rid),
    )
    conn.commit()
    return next_retry


def execute_replan(item):
    """
    ここは既存の replan 実処理に接続する。
    成功: True
    失敗: False（例外も False 扱い）
    """
    rid = item["replan_request_id"]
    print(f"[RETRY] START id={rid} tag={WORKER_TAG} stamp={FILE_STAMP}")

    try:
        # TODO: 実処理接続
        # result = real_replan(...)
        result = True
        return bool(result)
    except Exception as e:
        print(f"[RETRY] ERROR id={rid} error={type(e).__name__} tag={WORKER_TAG} stamp={FILE_STAMP}")
        return False


def retry_worker_once(conn):
    print(f"[WORKER] tick now={now_sql()} tag={WORKER_TAG} stamp={FILE_STAMP}")

    recover_stale_processing(conn)

    item = fetch_next_retry(conn)
    if not item:
        print(f"[WORKER] no_queued tag={WORKER_TAG} stamp={FILE_STAMP}")
        return

    rid = item["replan_request_id"]
    retry_count = int(item["retry_count"] or 0)
    max_retry = int(item["max_retry"] or 0)

    # ここで「処理前に上限超過」を裁く（無限ループ防止）
    if max_retry > 0 and retry_count >= max_retry:
        _mark_deadletter(conn, rid, "MaxRetryExceeded")
        print(f"[RETRY] DEADLETTER id={rid} retry_count={retry_count} max_retry={max_retry} tag={WORKER_TAG} stamp={FILE_STAMP}")
        return

    success = execute_replan(item)

    if success:
        _mark_done(conn, rid)
        print(f"[RETRY] DONE id={rid} tag={WORKER_TAG} stamp={FILE_STAMP}")
        return

    # 실패: 再試行 or deadletter
    # 失敗後に retry_count を増やす前提で、増加後に超過する場合も deadletter に落とす
    if max_retry > 0 and (retry_count + 1) >= max_retry:
        _mark_deadletter(conn, rid, "MaxRetryExceededAfterFail")
        print(f"[RETRY] DEADLETTER id={rid} retry_count={retry_count+1} max_retry={max_retry} tag={WORKER_TAG} stamp={FILE_STAMP}")
        return

    next_retry = _mark_retry_scheduled(conn, rid)
    print(f"[RETRY] RETRY_SCHEDULED id={rid} next_retry_at={next_retry} tag={WORKER_TAG} stamp={FILE_STAMP}")
