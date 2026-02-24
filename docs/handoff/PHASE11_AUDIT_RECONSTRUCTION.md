# Phase11 Audit Reconstruction Log

## 1. Summary

Phase11 established a reproducible path to attach outbox-derived events to the audit chain via the canonical contract, without dropping the DB and without breaking the existing 14 events.

Final evidence:

- verify_chain_v2: reachable length = 15
- TIP updated to the newly accepted event_id

## 2. Initial State

- Phase10 completed (canonical DB path fixed)
- Canonical DB:
  C:\Users\sirok\MoCKA\audit\ed25519\audit.db
- main_loop OK
- outbox OK (ai_ok confirmed)
- verify_chain_v2:
  reachable length = 14
  chain stops at GENESIS (partial)
- orphan: none (isolated)

## 3. Root Problem

accept_outbox_to_audit failed with:

sqlite3.OperationalError: no such column: prev_event_id

Cause:

- DB table audit_ledger_event has column: previous_event_id
- existing audit JSON uses: previous_event_id
- writer/accept implementation referenced: prev_event_id (mismatch)

Constraint:

- DO NOT DROP DB
- DO NOT destroy existing 14 events
- DO NOT change JSON chain format (audit/*.json contract semantics)

## 4. DB Schema Confirmation

PRAGMA table_info(audit_ledger_event) confirmed the ledger schema:

- event_id TEXT (PK)
- chain_hash TEXT NOT NULL
- previous_event_id TEXT NOT NULL DEFAULT 'GENESIS'
- event_content TEXT NOT NULL
- contract_version TEXT NOT NULL DEFAULT 'mocka.audit.v1'
- created_at TEXT NOT NULL

Key operational implication:

- INSERT must provide created_at (NOT NULL)
- the canonical column name is previous_event_id

## 5. Outbox Reality Check

Latest outbox artifacts were not canonical audit event JSON.

- outbox *_cycle_*.json: schema/run_id/ts_ms/stage/ok/summary/data/error (runtime cycle logs)
- outbox *_event.json: ts/event_kind/note (note packet), NOT audit event fields

Therefore, extracting event_id from outbox was impossible without canonical derivation.

## 6. Canonical Generator Discovery

Canonical derivation exists in:

- src.mocka_audit.contract_v1

Confirmed public API:

- compute_event_id(event_content: str) -> str
- compute_chain_hash(previous_event_id: str, current_event_id: str) -> str
- normalize_event_content(inp: AuditEventInput) -> str
- derive_event(inp: AuditEventInput, previous_event_id: str='GENESIS') -> AuditEventDerived

Contract enforcement:

- sha256_source and sha256_after must be 64 lowercase hex chars

## 7. Note Packet Acceptance Strategy

Goal: attach one new event to the current TIP to increase reachable length from 14 to 15.

Because note packet lacks sha256_source/sha256_after, the accepted method was:

- compact the note packet JSON deterministically
- compute SHA256(packet_json) as a 64-lowercase-hex string
- use that value for both sha256_source and sha256_after
- construct AuditEventInput with:
  - ts_local derived from outbox ts
  - event_kind from outbox event_kind (fallback 'note')
  - target_path as "outbox:<filename>"
  - contract_version = mocka.audit.v1
- call derive_event(inp, previous_event_id=TIP)

This produces canonical:
- event_content
- event_id computed from event_content under the contract rule
- chain_hash computed from previous_event_id and current_event_id under the contract rule

## 8. Ledger Insert (Observed Run Evidence)

A successful accepted event (values from the run):

- event_id:
  a837b19f1fa8c4e832f5ccf24934a7d9a8bf7f4ac76619b58753e06c9cc79bc1
- previous_event_id (TIP at the time):
  cc009711c19a8a9358bd282446f3cbcd3b834200ac5e7630e720bb820954b121
- chain_hash:
  1b87e65df554ef162fa4d1a8c5ab37b5a4134033fad0a427683939cb0084fe7e
- created_at:
  2026-02-20T11:26:32+09:00

Important: event_content must not be modified after deriving event_id.

## 9. Verification Source Mismatch (Key Discovery)

verify_chain_v2 does not read the DB ledger.

verify_chain_v2 reads only:

- audit/*.json
- audit/recovery/regenesis.json (regensis_event_id as TIP)

Therefore:

- DB-only insert does not change reachable length.
- file-chain sync and TIP update are required for verification to see the new event.

## 10. File Chain Sync and TIP Update

Actions performed:

1. Read event_content, previous_event_id, chain_hash, created_at from DB for the new event_id
2. Write audit/<event_id>.json using canonical fields:
   - event_id
   - previous_event_id
   - chain_hash
   - event_content
   - contract_version
   - created_at
3. Update audit/recovery/regenesis.json:
   - regensis_event_id = <new event_id>

## 11. Final Verification Result

verify_chain_v2 after sync:

- OK: reachable chain verified from TIP=<new event_id>
- OK: reachable length=15
- WARN: chain stopped at missing prev=GENESIS (partial)

GENESIS stop is expected and treated as partial-chain behavior by design.

## 12. Operational Conclusion

Phase11-A completion definition:

- A new outbox-derived event was canonically derived via contract_v1
- Stored in DB ledger without dropping DB and without breaking existing 14 events
- Synchronized to file-chain (audit/*.json) and TIP updated via regenesis.json
- verify_chain_v2 reachable length advanced from 14 to 15
