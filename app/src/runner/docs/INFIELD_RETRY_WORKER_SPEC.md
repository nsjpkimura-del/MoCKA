# INFIELD Retry Worker Specification (MoCKA 3.0)

## 1. Scope and Non-Scope
### 1.1 Scope
This document specifies structure, entrypoint control, configuration canon, and operational gates for INFIELD Retry Worker.

### 1.2 Non-Scope
- New feature additions beyond current behavior are out of scope.
- Database vendor changes are out of scope.
- External service redesign is out of scope.

## 2. Baseline Guarantees (assumed true)
1. Atomic fetch is implemented via UPDATE + RETURNING.
2. Concurrent dual start test succeeded.
3. Deadletter test succeeded.
4. Old runner is isolated and must not be referenced.
5. Periodic logging stop is confirmed.
6. The only canonical execution path is run_infield_retry_worker.cmd.

## 3. Canonical Execution Path (Entry Point Law)
### 3.1 Rule
Only run_infield_retry_worker.cmd may start the worker.

### 3.2 Entry Mark
The canonical entrypoint must set an environment mark:
- Variable: MOCKA_ENTRYPOINT
- Value: run_infield_retry_worker.cmd

### 3.3 Rejection
The python entry must reject any start without the entry mark.
The rejection must:
- Exit with non-zero code
- Emit a fixed log message containing: entrypoint missing

## 4. Configuration Canon (Config Canon)
### 4.1 Rule
Only mocka_orchestrator/.env is allowed.

### 4.2 No Auto-Discovery
Do not rely on dotenv auto-discovery. Load by explicit path.

### 4.3 Single Responsibility
Only one module/function is allowed to load config and export settings to the app layer.

## 5. Worker Behavior (invariants)
### 5.1 Atomic Fetch
The worker must claim work atomically using UPDATE + RETURNING.

### 5.2 Deadletter
Deadletter handling must remain functional and testable.

### 5.3 Concurrency
Starting two instances concurrently must be safe and must not double-claim work.

## 6. Regression Requirements (must always pass)
1. Concurrent dual start test passes.
2. Deadletter test passes.
3. Periodic logging remains disabled.
4. Structural SSOT checks pass (see ops/check_infield.ps1).