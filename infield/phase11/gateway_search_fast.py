import argparse
import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

DB_PATH = r"C:\Users\sirok\MoCKA\infield\phase11\knowledge.db"

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def get_event_columns(conn: sqlite3.Connection) -> List[str]:
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(events)")
    rows = cur.fetchall()
    return [r[1] for r in rows]

def parse_query_language(q: str) -> Tuple[Dict[str, str], str]:
    """
    Minimal / safe query language:
      Recognize key:value tokens for known keys.
      If key is not a real column in events, we DO NOT fail.
      Instead, we downgrade it into FTS term "value".

    Keys recognized: tag, cat, src, since
    since: is kept as filter only if events has a compatible column; otherwise downgraded to term.
    """
    tokens = q.strip().split()
    filters: Dict[str, str] = {}
    terms: List[str] = []

    for t in tokens:
        if ":" in t:
            k, v = t.split(":", 1)
            kl = k.lower().strip()
            vv = v.strip()
            if kl in ("tag", "cat", "src", "since") and vv != "":
                filters[kl] = vv
                continue
        terms.append(t)

    fts = " ".join(terms).strip()
    return filters, fts

def build_where_from_filters(filters: Dict[str, str], event_cols: List[str]) -> Tuple[List[str], List[Any], List[str]]:
    """
    Returns (where_parts, params, downgraded_terms)
    If a filter key does not exist in events table, downgrade to FTS term instead of failing.
    """
    where_parts: List[str] = []
    params: List[Any] = []
    downgraded_terms: List[str] = []

    for k, v in filters.items():
        if k in event_cols:
            where_parts.append(f"e.{k} = ?")
            params.append(v)
        else:
            # No such column in events: downgrade to term
            downgraded_terms.append(v)

    return where_parts, params, downgraded_terms

def search(conn: sqlite3.Connection, raw_query: str, top: int) -> Dict[str, Any]:
    conn.row_factory = sqlite3.Row
    event_cols = get_event_columns(conn)

    filters, fts_terms = parse_query_language(raw_query)
    where_parts, params, downgraded = build_where_from_filters(filters, event_cols)

    # If we downgraded filters (e.g. tag:phase11 but no tag column), add them to FTS terms
    merged_terms = " ".join([x for x in [fts_terms] if x] + downgraded).strip()

    cur = conn.cursor()

    # If no FTS terms, do table-only filtering
    if merged_terms == "":
        sql = "SELECT e.id AS id FROM events e"
        if where_parts:
            sql += " WHERE " + " AND ".join(where_parts)
        sql += " LIMIT ?"
        qparams = params[:] + [top]
        cur.execute(sql, qparams)
        rows = cur.fetchall()
        ids = [r["id"] for r in rows]
        return {
            "status": "SEARCH_OK",
            "generated_at_utc": utc_now_iso(),
            "count": len(ids),
            "ids": ids,
            "parsed": {
                "filters": filters,
                "fts_terms": merged_terms
            }
        }

    # FTS path: do not reference e.title or any optional column
    sql = """
    SELECT
        e.id AS id,
        bm25(events_fts) AS score
    FROM events_fts
    JOIN events e ON e.rowid = events_fts.rowid
    WHERE events_fts MATCH ?
    """
    qparams2: List[Any] = [merged_terms]

    if where_parts:
        sql += " AND " + " AND ".join(where_parts)
        qparams2.extend(params)

    sql += " ORDER BY score LIMIT ?"
    qparams2.append(top)

    cur.execute(sql, qparams2)
    rows = cur.fetchall()

    ids = [r["id"] for r in rows]
    return {
        "status": "SEARCH_OK",
        "generated_at_utc": utc_now_iso(),
        "count": len(ids),
        "ids": ids,
        "parsed": {
            "filters": filters,
            "fts_terms": merged_terms
        }
    }

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--top", type=int, default=20)
    args = ap.parse_args()

    if not os.path.isabs(DB_PATH):
        raise SystemExit("ERROR: DB_PATH must be absolute")

    conn = sqlite3.connect(DB_PATH)
    try:
        out = search(conn, args.query, args.top)
    finally:
        conn.close()

    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
