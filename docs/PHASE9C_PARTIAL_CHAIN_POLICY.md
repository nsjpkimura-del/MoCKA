MoCKA Phase9-C Partial Chain Policy

Location:
C:\Users\sirok\MoCKA\docs\PHASE9C_PARTIAL_CHAIN_POLICY.md

1. Canonical tip
- tip_event_id: cc009711c19a8a9358bd282446f3cbcd3b834200ac5e7630e720bb820954b121
- reachable_length: 14
- missing_prev: GENESIS

2. Declaration
- regenesis declaration file:
  C:\Users\sirok\MoCKA\audit\recovery\regenesis.json
- regensis_event_id must equal canonical tip.

3. Verification commands
- File chain verification:
  python -m src.mocka_audit.verify_chain
  expected:
  OK: partial allowed stopped_at_missing_prev=GENESIS length=14 tip=cc0097...

- Reachable-only verification:
  python -m src.mocka_audit.verify_chain_v2
  expected:
  OK: reachable chain verified from TIP=cc0097...
  OK: reachable length=14
  WARN: chain stopped at missing prev=GENESIS (partial)

4. Storage rules
- Canonical event json files must exist only under:
  C:\Users\sirok\MoCKA\audit\*.json

- Orphan / non-event files must be kept outside canonical set:
  C:\Users\sirok\MoCKA\audit\quarantine_orphans\
  C:\Users\sirok\MoCKA\audit\quarantine_non_events\

5. DB alignment
- DB path:
  C:\Users\sirok\MoCKA\audit\ed25519\audit.db

- DB ledger table:
  audit_ledger_event

- DB ledger must contain only event_ids reachable from canonical tip.

- Purge procedure:
  python tools\db_ledger_purge_orphans.py

- Purge report:
  C:\Users\sirok\MoCKA\audit\db_purge_report.txt

6. Invariants
- No self-reference events in canonical set.
- No loops in reachable chain.
- last_event_id.txt must be UTF-8 without BOM.
- GENESIS is not required; partial is formally accepted for Phase9-C.
- canonical tip_event_id must exist both as:
  (a) a JSON file under C:\Users\sirok\MoCKA\audit\
  (b) a row in the audit_ledger_event table within C:\Users\sirok\MoCKA\audit\ed25519\audit.db

7. Future events
- Any new event must reference the current canonical tip_event_id.
- last_event_id.txt must be updated atomically with event append.
- verify_chain must pass before deployment or distribution.
- verify_chain_v2 must confirm reachable_length consistency.
- DB ledger must be aligned with file canonical chain after any structural change.

8. Quick check (one-shot)
- Run:
  cd C:\Users\sirok\MoCKA
  python -m src.mocka_audit.verify_chain
  python -m src.mocka_audit.verify_chain_v2
  python tools\db_ledger_dump.py

- Expected:
  verify_chain shows partial ok with length=14 and the canonical tip.
  verify_chain_v2 shows reachable length=14 and missing prev=GENESIS.
  db_ledger_dump.tsv contains 14 rows and includes the canonical tip.