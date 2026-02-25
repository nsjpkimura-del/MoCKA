---

### event_type: REGISTER_BRANCH

Target Table:
branch_registry

Deterministic Structure:
- id (INTEGER PRIMARY KEY AUTOINCREMENT)
- created_utc (TEXT NOT NULL)
- tip_event_id (TEXT NOT NULL)
- orphan_event_id (TEXT NULL)
- orphan_prev_id (TEXT NULL)
- classification (TEXT NOT NULL)

Idempotency Rule:
INSERT only when a new (tip_event_id, orphan_event_id, orphan_prev_id, classification) tuple is not already present.
No UPDATE for this event_type. Existing equivalent row implies no-op.

Conflict Resolution:
If an equivalent tuple exists but classification differs, emit mismatch (do not apply).

Reversibility:
DELETE the inserted row by id (only if created by the current reconciliation attempt).

Hash Stability:
No hash column in this table.
Stability condition: deterministic tuple equality only.

---

### event_type: CLOSE_BRANCH

Target Table:
branch_registry

Deterministic Structure:
- id (INTEGER PRIMARY KEY AUTOINCREMENT)
- created_utc (TEXT NOT NULL)
- tip_event_id (TEXT NOT NULL)
- orphan_event_id (TEXT NULL)
- orphan_prev_id (TEXT NULL)
- classification (TEXT NOT NULL)

Idempotency Rule:
No-op (branch_registry has no close marker column).

Conflict Resolution:
Emit mismatch if governance emits CLOSE_BRANCH but no proof close-state exists.
Do not apply.

Reversibility:
Not applicable (no mutation).

Hash Stability:
No hash column. No mutation.

---

### event_type: ANCHOR_PROOF

Target Table:
proof_anchor

Deterministic Structure:
- anchor_id (TEXT PRIMARY KEY)
- governance_event_id (TEXT NOT NULL)
- anchor_hash (TEXT NOT NULL)
- created_utc (TEXT NOT NULL)

Idempotency Rule:
INSERT OR IGNORE by anchor_id

Conflict Resolution:
If target table is missing -> mismatch (do not apply).
If existing row hash differs -> mismatch (do not apply).

Reversibility:
DELETE WHERE anchor_id = ? (only if created by current reconciliation attempt)

Hash Stability:
anchor_hash = SHA256(governance_event_id + anchor_id)
