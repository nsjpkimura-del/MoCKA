import sqlite3, datetime

db = r'C:\Users\sirok\MoCKA\infield\state\mocka_state.db'
con = sqlite3.connect(db)
cur = con.cursor()

now = datetime.datetime.utcnow().isoformat()

cur.execute("""
INSERT INTO retry_queue (
    replan_request_id,
    event_id,
    plan_rev,
    provider_name,
    error_class,
    retry_count,
    max_retry,
    next_retry_at,
    status,
    last_status_updated_at
)
VALUES (?,?,?,?,?,?,?,?,?,?)
""", (
    "R-TEST-" + now,
    "EVT-TEST",
    1,
    "openai",
    "",
    0,
    3,
    now,          # 今すぐ実行可能
    "queued",
    now
))

con.commit()
con.close()

print("Injected test retry row.")
