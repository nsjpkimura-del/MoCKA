import argparse
import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from openpyxl import Workbook
except Exception:
    Workbook = None


DB_PATH = r"C:\Users\sirok\MoCKA\infield\phase11\knowledge.db"
OUTBOX_DIR = r"C:\Users\sirok\MoCKA\outbox"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def normalize_json_arg(s: str) -> str:
    """
    PowerShell/IME/クリップボード経由で混入しがちな不可視文字を除去してから JSON として扱う。
    - 前後空白
    - UTF-8 BOM
    - 先頭末尾の不正な引用符が二重に付いたケース
    """
    if s is None:
        return s
    t = s.strip()
    t = t.lstrip("\ufeff")
    # たまに全角引用符などが混ざるので最低限の置換
    t = t.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    # 引数がさらに引用されて渡ってきた場合に外す
    if len(t) >= 2 and ((t[0] == "'" and t[-1] == "'") or (t[0] == '"' and t[-1] == '"')):
        inner = t[1:-1].strip().lstrip("\ufeff")
        # inner が JSON 配列っぽいなら採用
        if inner.startswith("[") and inner.endswith("]"):
            t = inner
    return t


def load_ids_from_json_arg(ids_json: str) -> List[str]:
    ids_json = normalize_json_arg(ids_json)
    try:
        obj = json.loads(ids_json)
    except Exception as e:
        raise ValueError(f"ids_json is not valid JSON: {e}. raw={repr(ids_json)}") from e

    if not isinstance(obj, list):
        raise ValueError("ids_json must be a JSON array")

    ids: List[str] = []
    for x in obj:
        if isinstance(x, (str, int)):
            ids.append(str(x))
        else:
            raise ValueError("ids_json elements must be string/int")
    return ids


def load_ids_from_file(path: str) -> List[str]:
    if not os.path.isabs(path):
        raise ValueError("ids_file must be absolute path")

    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    raw_strip = normalize_json_arg(raw).strip()
    if raw_strip.startswith("[") and raw_strip.endswith("]"):
        return load_ids_from_json_arg(raw_strip)

    ids: List[str] = []
    for line in raw.splitlines():
        s = line.strip()
        if s:
            ids.append(s)
    return ids


def get_table_columns(conn: sqlite3.Connection, table_name: str) -> List[str]:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    cols = []
    for row in cur.fetchall():
        cols.append(row[1])
    return cols


def fetch_event_by_id(conn: sqlite3.Connection, columns: List[str], event_id: str) -> Optional[Dict[str, Any]]:
    cur = conn.cursor()
    col_sql = ", ".join([f'"{c}"' for c in columns])
    cur.execute(f'SELECT {col_sql} FROM events WHERE id = ?', (event_id,))
    row = cur.fetchone()
    if row is None:
        return None

    item: Dict[str, Any] = {}
    for idx, c in enumerate(columns):
        item[c] = row[idx]
    return item


def compute_integrity_recalc(event: Dict[str, Any]) -> str:
    if "content" in event and event["content"] is not None:
        return sha256_text(str(event["content"]))
    canonical = json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256_text(canonical)


def write_xlsx_evidence(path: str, batch: List[Dict[str, Any]], ordered_columns: List[str]) -> None:
    if Workbook is None:
        raise RuntimeError("openpyxl is not available")

    wb = Workbook()
    ws = wb.active
    ws.title = "events"

    ws.append(ordered_columns)

    for e in batch:
        row = []
        for c in ordered_columns:
            v = e.get(c, None)
            if isinstance(v, (dict, list)):
                row.append(json.dumps(v, ensure_ascii=False))
            else:
                row.append(v)
        ws.append(row)

    wb.save(path)


def build_proof(ids: List[str], batch: List[Dict[str, Any]]) -> Dict[str, Any]:
    ids_hash = sha256_text("\n".join(ids))
    canonical_batch = json.dumps(batch, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    batch_hash = sha256_text(canonical_batch)
    return {
        "ids_count": len(ids),
        "ids_hash": ids_hash,
        "batch_hash": batch_hash,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="MoCKA Phase11 gateway_get_batch")
    parser.add_argument("-ids_json", default=None)
    parser.add_argument("-ids_file", default=None)
    parser.add_argument("-out_json", default=None)
    parser.add_argument("-xlsx", action="store_true")
    parser.add_argument("-limit", type=int, default=None)
    args = parser.parse_args()

    if args.ids_json is None and args.ids_file is None:
        raise SystemExit("ERROR: Provide -ids_json or -ids_file")
    if args.ids_json is not None and args.ids_file is not None:
        raise SystemExit("ERROR: Provide only one of -ids_json or -ids_file")

    ensure_dir(OUTBOX_DIR)

    if args.ids_json is not None:
        ids = load_ids_from_json_arg(args.ids_json)
    else:
        ids = load_ids_from_file(args.ids_file)

    if args.limit is not None and len(ids) > args.limit:
        raise SystemExit(f"ERROR: ids count {len(ids)} exceeds -limit {args.limit}")

    conn = sqlite3.connect(DB_PATH)
    columns = get_table_columns(conn, "events")

    core_order = ["id", "title", "content", "tag", "cat", "src", "created_at_utc", "created_at", "ts_utc", "ts"]
    ordered_columns: List[str] = []
    for c in core_order:
        if c in columns and c not in ordered_columns:
            ordered_columns.append(c)
    for c in columns:
        if c not in ordered_columns:
            ordered_columns.append(c)

    batch: List[Dict[str, Any]] = []
    missing: List[str] = []

    for event_id in ids:
        ev = fetch_event_by_id(conn, ordered_columns, event_id)
        if ev is None:
            missing.append(event_id)
            continue
        ev["integrity_recalc"] = compute_integrity_recalc(ev)
        batch.append(ev)

    conn.close()

    proof = build_proof(ids, batch)

    payload: Dict[str, Any] = {
        "mode": "getbatch",
        "generated_at_utc": utc_now_iso(),
        "fixed_ids_order": ids,
        "missing_ids": missing,
        "proof": proof,
        "batch": batch,
    }

    if args.out_json is not None:
        if not os.path.isabs(args.out_json):
            raise SystemExit("ERROR: -out_json must be absolute path")
        out_json_path = args.out_json
        out_dir = os.path.dirname(out_json_path)
        if out_dir:
            ensure_dir(out_dir)
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out_json_path = os.path.join(OUTBOX_DIR, f"getbatch_{ts}.json")

    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    xlsx_path = None
    if args.xlsx:
        base_dir = os.path.dirname(out_json_path) if os.path.dirname(out_json_path) else OUTBOX_DIR
        base_name = os.path.splitext(os.path.basename(out_json_path))[0]
        xlsx_path = os.path.join(base_dir, f"{base_name}.xlsx")
        write_xlsx_evidence(xlsx_path, batch, ordered_columns + ["integrity_recalc"])

    print("OUTPUT_JSON:", out_json_path)
    if xlsx_path is not None:
        print("OUTPUT_XLSX:", xlsx_path)
    if missing:
        print("MISSING_IDS_COUNT:", len(missing))


if __name__ == "__main__":
    main()
