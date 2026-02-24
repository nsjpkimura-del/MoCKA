# C:\Users\sirok\MoCKA\audit\ed25519\governance\fix_backup_index_csv.py
# note: Phase14.6 normalize backup_index.csv

import os

ROOT = r"C:\Users\sirok\MoCKA"
CSV_PATH = os.path.join(ROOT, "audit", "ed25519", "governance", "backup_index.csv")

HEADER = "timestamp_utc,backup_id,artifact_path,sha256_hex,event_id,note"
INIT_NOTE = "note: Phase14.6 CSV init (backup_index)"

def main():
    if not os.path.exists(CSV_PATH):
        print("CSV_NOT_FOUND")
        return

    with open(CSV_PATH, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()

    lines = []
    for ln in raw.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        s = ln.strip()
        if not s:
            continue
        lines.append(s)

    normalized = [HEADER, INIT_NOTE]

    for s in lines:
        if s == HEADER or s == INIT_NOTE:
            continue

        if s.startswith(INIT_NOTE + "20") and s.count(",") >= 5:
            s = s[len(INIT_NOTE):].lstrip()

        if s.startswith("20") and s.count(",") >= 5:
            normalized.append(s)
            continue

        normalized.append("note: preserved_unparsed_line: " + s)

    out = "\n".join(normalized) + "\n"
    with open(CSV_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)

    print("OK: backup_index.csv normalized")
    print("PATH:", CSV_PATH)

if __name__ == "__main__":
    main()