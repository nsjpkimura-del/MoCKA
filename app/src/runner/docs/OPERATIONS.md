# Operations: INFIELD Retry Worker (MoCKA 3.0)

## 1. Canonical Start/Stop
### 1.1 Start
Use only:
- run_infield_retry_worker.cmd

### 1.2 Stop
Document stop procedures without introducing alternate startup scripts.

## 2. Verification Gate (mandatory)
Before considering any change valid, run:
- ops/check_infield.ps1

A change is valid only if:
- Structural checks pass
- Regression checks pass

## 3. Incident Handling (minimal protocol)
### 3.1 Symptoms
- Worker does not pick jobs
- Deadletter grows unexpectedly
- Duplicate processing observed
- Unexpected periodic logs resume

### 3.2 Immediate Actions
1. Stop all worker processes started by the canonical entrypoint.
2. Run ops/check_infield.ps1 to detect structural drift.
3. Re-start using canonical entrypoint only.

### 3.3 Record
Append what happened and verification results to docs/CHANGELOG_INFIELD.md.

## 4. Forbidden Actions
- Creating new startup scripts
- Adding new .env files anywhere
- Running python entry directly without entry mark
- Reintroducing old runner paths