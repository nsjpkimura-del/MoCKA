# MoCKA 3.0 SSOT (Single Source of Truth)

## 1. Scope
This registry defines the single sources of truth (SSOT) for MoCKA 3.0 INFIELD Retry Worker.
Any change that violates this registry is invalid.

## 2. Canonical Sources

### 2.1 Execution Canon (single entrypoint)
- Canonical entrypoint: run_infield_retry_worker.cmd
- Any other startup path is invalid.

### 2.2 Configuration Canon (single .env)
- Canonical .env: mocka_orchestrator/.env (this file only)
- Any other .env under the repository tree is invalid.

### 2.3 Operational Canon
- docs/OPERATIONS.md
- ops/check_infield.ps1

### 2.4 Design Canon
- docs/INFIELD_RETRY_WORKER_SPEC.md

## 3. Prohibitions (hard rules)
1. Any .env outside mocka_orchestrator/.env is prohibited.
2. Any entrypoint other than run_infield_retry_worker.cmd is prohibited.
3. Direct execution of python entry without the entrypoint mark is prohibited.
4. Revival or reference of the old mocka-infield runner is prohibited.
5. Revival of periodic logging is prohibited.

## 4. Change Procedure (mandatory)
1. Record reason and verification results in docs/CHANGELOG_INFIELD.md.
2. Pass ops/check_infield.ps1 with no violations.
3. Changes that fail checks are invalid and must not be merged or deployed.