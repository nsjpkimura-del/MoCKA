# ORPHAN_CLASSIFICATION_20260223

## TYPE A: Outbox Non-Audit Events
- 43a48e0c...
- fd58dcfa...

Reason:
Not part of audit ledger chain.
Should be stored under outbox, not audit root.

## TYPE B: Revocation Branch (Test Fork)
- 47e418f1...
- e18714e3...
- 53499d03...

Reason:
Temporary revocation test branch.
Not adopted into final TIP.
Represents historical fork.

Action:
No deletion in Phase13.
Cleanup deferred to Phase14.
