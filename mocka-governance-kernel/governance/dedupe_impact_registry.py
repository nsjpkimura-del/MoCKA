# C:\Users\sirok\MoCKA\audit\ed25519\governance\dedupe_impact_registry.py
# note: Phase14.6 dedupe impact_registry.csv (preserve order, remove exact duplicates)

import os

ROOT = r"C:\Users\sirok\MoCKA"
CSV_PATH = os.path.join(ROOT, "audit", "ed25519", "governance", "impact_registry.csv")

def main():
    if not os.path.exists(CSV_PATH):
        print("CSV_NOT_FOUND")
        return

    with open(CSV_PATH, "r", encoding="utf-8", errors="replace") as f:
        lines = f.read().replace("\r\n", "\n").replace("\r", "\n").split("\n")

    out = []
    seen = set()
    removed = 0

    for ln in lines:
        s = ln.strip()
        if not s:
            continue

        # keep header + init note always (but still avoid duplicates)
        key = s
        if key in seen:
            removed += 1
            continue
        seen.add(key)
        out.append(s)

    with open(CSV_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")

    print("OK: impact_registry deduped")
    print("REMOVED_LINES:", removed)

if __name__ == "__main__":
    main()