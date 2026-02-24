# C:\Users\sirok\MoCKA\audit\ed25519\governance\fix_change_log_csv.py
# note: Phase14.6 fix change_log.csv newline corruption

import os

ROOT = r"C:\Users\sirok\MoCKA"
CSV_PATH = os.path.join(ROOT, "audit", "ed25519", "governance", "change_log.csv")

HEADER = "timestamp_utc,event_type,event_id,prev_event_id,note"
INIT_NOTE = "note: Phase14.6 CSV init (change_log)"

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

    normalized = []
    normalized.append(HEADER)
    normalized.append(INIT_NOTE)

    for s in lines:
        if s == HEADER:
            continue
        if s == INIT_NOTE:
            continue

        # header+initnote+data が1行に潰れているケースを救済
        if s.startswith(INIT_NOTE + "20") and ",TIP_UPDATE," in s:
            s = s[len(INIT_NOTE):].lstrip()

        if s.startswith("20") and ",TIP_UPDATE," in s:
            normalized.append(s)
            continue

        # 想定外行は note として保持（証跡を捨てない）
        normalized.append("note: preserved_unparsed_line: " + s)

    out = "\n".join(normalized) + "\n"
    with open(CSV_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)

    print("OK: change_log.csv normalized")
    print("PATH:", CSV_PATH)

if __name__ == "__main__":
    main()