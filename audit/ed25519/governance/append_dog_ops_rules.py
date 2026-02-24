# C:\Users\sirok\MoCKA\audit\ed25519\governance\append_dog_ops_rules.py
# note: Phase14.6 append ops rules to DOG (decision-before-action protocol)

import os
from datetime import datetime

ROOT = r"C:\Users\sirok\MoCKA"
DOG_PATH = os.path.join(ROOT, "docs", "DOG_PHASE14.6_DUAL_LAYER_MCGS.md")

BLOCK = f"""
## 6. Governance Operation Protocol (Fixed)
note: Decision-before-action protocol is mandatory.

### 6.1 Rule
1. Record a governance decision event first (governance.db).
2. Execute proof-side action second (audit.db and files), without schema changes.
3. Append human-readable logs third (CSV and DOG if needed).
4. Verify governance chain after each governance write.

### 6.2 Command Order Templates
A) TIP reselect
1) python audit\\ed25519\\governance\\governance_ops.py tip_reselect @audit\\ed25519\\governance\\payload_tip_reselect_ops.json "note: ..."
2) python tools\\phase14_reselect_tip.py
3) python audit\\ed25519\\governance\\governance_chain_verify.py
4) python audit\\ed25519\\governance\\governance_csv_append.py

B) Classification change
1) python audit\\ed25519\\governance\\governance_ops.py classify @payload.json "note: ..."
2) run proof-side classification tool (no schema change)
3) python audit\\ed25519\\governance\\governance_chain_verify.py

C) Quarantine / release
1) python audit\\ed25519\\governance\\governance_ops.py quarantine @payload.json "note: ..."
2) run proof-side quarantine tool and snapshot
3) python audit\\ed25519\\governance\\governance_chain_verify.py
4) update impact_registry / backup_index if artifacts changed

### 6.3 Append Record
Appended(JST): {datetime.now().strftime("%Y-%m-%d")}
note: Phase14.6 DOG updated to include fixed operation protocol.
"""

def main():
    if not os.path.exists(DOG_PATH):
        print("DOG_NOT_FOUND")
        return

    with open(DOG_PATH, "r", encoding="utf-8", errors="replace") as f:
        cur = f.read()

    if "## 6. Governance Operation Protocol (Fixed)" in cur:
        print("ALREADY_PRESENT")
        return

    with open(DOG_PATH, "a", encoding="utf-8", newline="\n") as f:
        if not cur.endswith("\n"):
            f.write("\n")
        f.write(BLOCK.strip() + "\n")

    print("OK: DOG appended ops rules")
    print("PATH:", DOG_PATH)

if __name__ == "__main__":
    main()