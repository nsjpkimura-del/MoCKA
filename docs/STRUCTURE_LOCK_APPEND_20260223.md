# STRUCTURE_LOCK_APPEND_20260223

## DB is Single Source of Truth
verify_chain_db.py uses audit.db only.
JSON files are legacy artifacts.

## Layer Separation
audit/  -> ledger events only
outbox/ -> generation logs only

## No Cross Mixing Allowed
audit must not contain mocka.outbox schema.
verify must not scan JSON files.

Status: STRUCTURE STABILIZED
