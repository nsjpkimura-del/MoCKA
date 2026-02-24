\# PHASE14.6 Branch Registry Schema Initialization Note



\## Date

2026-02-24



\## Context

Phase14.6 audit check failed at section:

\[2] Proof branch guard report

Return code: 3



Cause:

The SQLite table `branch\_registry` did not exist in:



C:\\Users\\sirok\\MoCKA\\audit\\ed25519\\audit.db



The guard report expects a table, not a JSON file.



\## Action Taken

Executed schema initialization:



CREATE TABLE IF NOT EXISTS branch\_registry (

&nbsp;   id INTEGER PRIMARY KEY AUTOINCREMENT,

&nbsp;   created\_utc TEXT NOT NULL,

&nbsp;   tip\_event\_id TEXT NOT NULL,

&nbsp;   orphan\_event\_id TEXT,

&nbsp;   orphan\_prev\_id TEXT,

&nbsp;   classification TEXT NOT NULL

);



Indexes added:

\- idx\_branch\_registry\_tip

\- idx\_branch\_registry\_class



No rows inserted.



\## Institutional Impact

\- Governance chain: unchanged

\- TIP: unchanged

\- Proof ledger: unchanged

\- CSV anchoring: unchanged

\- Determinism: preserved



This was a schema compatibility correction only.



\## Verification

Command:

python .\\tools\\phase14\_6\_audit\_check.py



Result:

OK: Phase14.6 audit check passed

