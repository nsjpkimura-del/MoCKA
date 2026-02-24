# C:\Users\sirok\MoCKA\audit\ed25519\governance\normalize_impact_registry_paths.py
# note: Phase14.6 normalize impact_registry artifact_path (remove \.\)

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
    changed = 0
    for ln in lines:
        if not ln.strip():
            continue
        fixed = ln.replace(r"\.\audit", r"\audit").replace(r"\.\docs", r"\docs")
        if fixed != ln:
            changed += 1
        out.append(fixed)

    with open(CSV_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")

    print("OK: impact_registry paths normalized")
    print("CHANGED_LINES:", changed)

if __name__ == "__main__":
    main()