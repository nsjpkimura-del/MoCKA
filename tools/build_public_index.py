#!/usr/bin/env python3
import csv
import json
import sys

INDEX_PATH = "governance/history_index.csv"
OUT_PATH = "governance/propagation/public_index_v1.json"

ELIG_IMPORTANCE = {"A", "B"}
ELIG_STATUS = {"Active"}

PUBLIC_FIELDS = [
    "event_id",
    "date",
    "event_type",
    "title_20",
    "summary_100",
    "importance",
    "status",
]

OPTIONAL_FIELDS = [
    "canonical_path",
    "content_hash",
]

def main() -> None:
    rows = []
    with open(INDEX_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if not r:
                continue
            if (r.get("importance") or "").strip() not in ELIG_IMPORTANCE:
                continue
            if (r.get("status") or "").strip() not in ELIG_STATUS:
                continue

            item = {}
            for k in PUBLIC_FIELDS:
                item[k] = (r.get(k) or "").strip()
            for k in OPTIONAL_FIELDS:
                v = (r.get(k) or "").strip()
                if v:
                    item[k] = v
            rows.append(item)

    payload = {
        "schema_version": "1.0",
        "generated_from": INDEX_PATH,
        "count": len(rows),
        "items": rows,
    }

    import os
    os.makedirs("governance/propagation", exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    sys.stdout.write(f"OK wrote {OUT_PATH} items={len(rows)}\n")

if __name__ == "__main__":
    main()
