import os
import json
import sqlite3

ROOT = r"C:/Users/sirok/MoCKA"

def scan_db(path):
    result = {
        "db_path": path,
        "has_audit_ledger_event": False,
        "row_count": 0,
        "latest_created_at_utc": None,
        "latest_chain_hash": None,
    }

    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()

        # テーブル存在確認
        cur.execute(
            "select name from sqlite_master where type='table' and name='audit_ledger_event'"
        )
        if not cur.fetchone():
            conn.close()
            return result

        result["has_audit_ledger_event"] = True

        # 件数
        cur.execute("select count(*) from audit_ledger_event")
        result["row_count"] = cur.fetchone()[0]

        # 最新レコード
        cur.execute(
            "select created_at_utc, chain_hash from audit_ledger_event order by id desc limit 1"
        )
        row = cur.fetchone()
        if row:
            result["latest_created_at_utc"] = row[0]
            result["latest_chain_hash"] = row[1]

        conn.close()

    except Exception as e:
        result["error"] = str(e)

    return result


def main():
    findings = []

    for root, dirs, files in os.walk(ROOT):
        for f in files:
            if f.endswith(".db"):
                full_path = os.path.join(root, f)
                findings.append(scan_db(full_path))

    print(json.dumps(findings, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()