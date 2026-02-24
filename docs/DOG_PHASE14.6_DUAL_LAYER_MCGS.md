\# DOG\_PHASE14.6\_DUAL\_LAYER\_MCGS

note: Phase14.6 Dual-Layer Governance Architecture DOG (Human-readable layer)



Document: DOG\_PHASE14.6\_DUAL\_LAYER\_MCGS

Version: 1.0

Created(JST): 2026-02-24

Author: nsjp\_kimura



\## 1. Purpose

Establish Dual-Layer Governance Architecture.

Proof Ledger (audit.db) remains non-invasive.

Governance Ledger (governance.db) records decisions and development governance as an append-only hash chain.

Human-readable docs (this DOG and CSV) provide reversible restoration for humans.



\## 2. Layer Definitions

Layer 1: Proof Ledger

Path: C:\\Users\\sirok\\MoCKA\\audit\\ed25519\\audit.db

Rule: No schema changes in Phase14.6.



Layer 2: Governance Ledger

Path: C:\\Users\\sirok\\MoCKA\\audit\\ed25519\\governance\\governance.db

Table: governance\_ledger\_event

Rule: Append-only. Chain verification required.



Layer 3: Human-readable Docs

Path:

\- C:\\Users\\sirok\\MoCKA\\docs\\DOG\_PHASE14.6\_DUAL\_LAYER\_MCGS.md

\- C:\\Users\\sirok\\MoCKA\\audit\\ed25519\\governance\\change\_log.csv

\- C:\\Users\\sirok\\MoCKA\\audit\\ed25519\\governance\\impact\_registry.csv

\- C:\\Users\\sirok\\MoCKA\\audit\\ed25519\\governance\\backup\_index.csv



\## 3. Fixed Facts (Evidence)

Proof TIP (Phase14 selected):

33cedbb94b557e08c1babf10006f288c112e26b2ecd4cb563458ff632f3b07d9



Governance GENESIS created:

EVENT\_ID: c4998d316826648016d9f896597084cf05ceadcd81d6a136f4efa9b23851a1ea

CHAIN\_HASH: 96287106682a59ea85d385c7dc75d78ccb38b426549734ca55a3f1ad1f6d5bf6



PHASE\_TRANSITION appended:

EVENT\_ID: 16ebe8ae8f82d458298cba99d3fa5b431106bf72a42bda46d54aa4eb72b4269b

TIP\_CHAIN\_HASH(after append):

1b6689b60732239cbbfd54708f242b482881c89364a5f2c5458ef83ffaaabb7e



Governance chain verification:

Status: OK

Rows: 2



\## 4. Operational Rules

1\. Any governance action must be written to governance.db first.

2\. CSV is derived for readability; authenticity is anchored in governance.db chain.

3\. Proof Ledger is never modified by governance operations.

4\. When TIP is reselected or classification changes occur, record a governance event before applying operational changes.



\## 5. Next Steps

\- Implement governance CLI for append (writer wrapper) and verify.

\- Add event types for classification change, quarantine action, tip reselect, and backup index.

## 6. Governance Operation Protocol (Fixed)
note: Decision-before-action protocol is mandatory.

### 6.1 Rule
1. Record a governance decision event first (governance.db).
2. Execute proof-side action second (audit.db and files), without schema changes.
3. Append human-readable logs third (CSV and DOG if needed).
4. Verify governance chain after each governance write.

### 6.2 Command Order Templates
A) TIP reselect
1) python audit\ed25519\governance\governance_ops.py tip_reselect @audit\ed25519\governance\payload_tip_reselect_ops.json "note: ..."
2) python tools\phase14_reselect_tip.py
3) python audit\ed25519\governance\governance_chain_verify.py
4) python audit\ed25519\governance\governance_csv_append.py

B) Classification change
1) python audit\ed25519\governance\governance_ops.py classify @payload.json "note: ..."
2) run proof-side classification tool (no schema change)
3) python audit\ed25519\governance\governance_chain_verify.py

C) Quarantine / release
1) python audit\ed25519\governance\governance_ops.py quarantine @payload.json "note: ..."
2) run proof-side quarantine tool and snapshot
3) python audit\ed25519\governance\governance_chain_verify.py
4) update impact_registry / backup_index if artifacts changed

### 6.3 Append Record
Appended(JST): 2026-02-24
note: Phase14.6 DOG updated to include fixed operation protocol.
