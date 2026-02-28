import csv
import os

BASE = r"C:\Users\sirok\MoCKA\governance\infield\index"
FILES = ["seeds_index.csv", "docs_index.csv", "calc_index.csv"]
NEW_COLUMNS = ["supersedes", "verified"]

for fname in FILES:
    path = os.path.join(BASE, fname)
    rows = []

    with open(path, "r", newline="", encoding="utf-8") as r:
        reader = csv.DictReader(r)
        fieldnames = list(reader.fieldnames)

        for col in NEW_COLUMNS:
            if col not in fieldnames:
                fieldnames.append(col)

        for row in reader:
            for col in NEW_COLUMNS:
                if col not in row:
                    row[col] = ""
            rows.append(row)

    with open(path, "w", newline="", encoding="utf-8") as w:
        writer = csv.DictWriter(w, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

print("INDEX_COLUMNS_UPDATED")
