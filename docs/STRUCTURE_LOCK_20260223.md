# STRUCTURE_LOCK_20260223

canonical_entry: C:\Users\sirok\MoCKA\main_loop.py
delete_policy: phase14_only
rename_policy: phase14_only
inventory_required: true

layers:
- launcher: env + path only
- core: audit + contract + db
- field: execution only

forbidden:
- launcher writes db
- field computes chain_hash
- field generates event_id
- core depends on launcher
