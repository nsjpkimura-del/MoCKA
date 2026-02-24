\# PHASE15\_PROOF\_DICTIONARY

Deterministic Governance → Proof Mutation Contract



Status: DRAFT

Tag: phase15-dictionary-v1



---



\## 0. Purpose



This document defines the canonical mapping between:



Governance event\_type

→ Deterministic Proof DB mutation



No auto-apply is permitted unless defined here.



---



\## 1. Global Invariants



\- Governance DB is read-only.

\- Proof DB mutations must be deterministic.

\- All mutations must be idempotent.

\- Every mutation must be reversible.

\- Hash stability must be preserved.



---



\## 2. Event Type Definitions



---



\### event\_type: REGISTER\_BRANCH



Target Table:

branch\_registry



Deterministic Structure:

\- branch\_id (TEXT PRIMARY KEY)

\- governance\_event\_id (TEXT)

\- created\_at (INTEGER)

\- branch\_hash (TEXT)



Idempotency Rule:

INSERT OR IGNORE by branch\_id



Conflict Resolution:

If existing row hash != computed hash → mismatch



Reversibility:

DELETE WHERE branch\_id = ?



Hash Stability:

branch\_hash = SHA256(branch\_id + governance\_event\_id)



---



\### event\_type: CLOSE\_BRANCH



Target Table:

branch\_registry



Deterministic Structure:

\- closed\_at (INTEGER)



Idempotency Rule:

UPDATE only if closed\_at IS NULL



Conflict Resolution:

If already closed → no-op



Reversibility:

Set closed\_at = NULL



Hash Stability:

No hash mutation allowed



---



\### event\_type: ANCHOR\_PROOF



Target Table:

proof\_anchor



Deterministic Structure:

\- anchor\_id (TEXT PRIMARY KEY)

\- governance\_event\_id (TEXT)

\- anchor\_hash (TEXT)

\- created\_at (INTEGER)



Idempotency Rule:

INSERT OR IGNORE by anchor\_id



Conflict Resolution:

Hash mismatch → reconciliation required



Reversibility:

DELETE WHERE anchor\_id = ?



Hash Stability:

anchor\_hash = SHA256(governance\_event\_id + anchor\_id)



---



\## 3. Dictionary Freeze Rule



Before enabling apply-mode:



1\. Tag repository with:

&nbsp;  phase15-dictionary-v1



2\. Verify no modifications to this file.



---



\## 4. Expansion Policy



New event\_type must define:



\- Target table

\- Deterministic schema

\- Idempotency

\- Conflict resolution

\- Reversibility

\- Hash stability formula



Without full definition:

→ enforce-mode forbidden

