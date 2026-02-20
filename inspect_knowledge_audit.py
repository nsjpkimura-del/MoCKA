import sqlite3
import json

DB = r"C:/Users/sirok/MoCKA/infield/phase11/db/knowledge.db"

result = {
    "table_exists": False,
    "schema": None,
    "columns": [],
    "row_count": 0,
    "sample_rows": []
}

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("select name from sqlite_master where type='table' and name='audit_ledger_event'")
if cur.fetchone():
    result["table_exists"] = True

    cur.execute("select sql from sqlite_master where type='table' and name='audit_ledger_event'")
    row = cur.fetchone()
    if row:
        result["schema"] = row[0]

    cur.execute("pragma table_info(audit_ledger_event)")
    result["columns"] = cur.fetchall()

    cur.execute("select count(*) from audit_ledger_event")
    result["row_count"] = cur.fetchone()[0]

    cur.execute("select * from audit_ledger_event limit 3")
    result["sample_rows"] = cur.fetchall()

conn.close()

print(json.dumps(result, indent=2, default=str))