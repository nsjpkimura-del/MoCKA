# MoCKA Phase14 Branch \& Orphan Policy (Draft)

## Objective

Define deterministic branch selection and orphan handling rules.

## Definitions

* TIP: current canonical chain head
* Orphan Event: event not reachable from TIP
* Branch: alternative reachable chain path

## Required Controls

1. Orphan detection routine
2. Deterministic TIP selection rule
3. Branch logging registry
4. Conflict resolution protocol

## Implementation Targets

* src.mocka\_audit.branch\_manager (new module)
* tools.detect\_orphans.py
* tools.reselect\_tip.py

Status: DESIGN INIT


## Evidence: orphan scan output (paste raw)
NOTE: Paste the raw stdout from tools\phase14_detect_orphans.py here.
## Evidence: quarantine procedure
Timestamp (UTC): 2026-02-24 02:12:11
Paste the raw stdout from:
- tools\phase14_quarantine_orphan.py
- tools\phase14_branch_guard_report.py
- tools\phase14_update_classification.py (restore)
below.
