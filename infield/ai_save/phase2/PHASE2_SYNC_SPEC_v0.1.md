# PHASE2_SYNC_SPEC_v0.1

NOTE: Purpose
- Extract append-only diffs from infield/ai_save/index.csv
- Emit append-only sync packets into infield/ai_save/outbox as JSON Lines (jsonl)
- External brains (Sheets/Firebase/etc.) must read outbox and append; never rewrite local history

NOTE: Invariants
- index.csv is append-only
- outbox packets are append-only
- No external system may modify index.csv directly

NOTE: Packet format (one JSON object per line)
{
  "packet_version": "0.1",
  "run_id": "<UTC yyyymmdd_HHMMSS>",
  "seq": <integer>,
  "source": {
    "path": "infield/ai_save/index.csv",
    "line_no": <integer>
  },
  "row": { "<header>": "<value>", ... },
  "row_hash": "sha256:<hex>",
  "observed_at": "<ISO8601 local time>"
}

NOTE: State tracking
- Diff cursor (last processed line_no):
  C:\Users\sirok\MoCKA\infield\ai_save\phase2\diff_state.json
- Re-run is idempotent: only new lines beyond last_line_no are emitted

NOTE: Seal checkpoint
- Last chain hash for external sync checkpoint:
  C:\Users\sirok\MoCKA\infield\ai_save\phase2\state.json

NOTE: Security
- outbox stays local (infield default ignore); do not add to public Git

NOTE: Phase2 run sequence (one-shot)
1) diff extract:
  powershell -ExecutionPolicy Bypass -File C:\Users\sirok\MoCKA\infield\ai_save\phase2\diff_extract.ps1
2) seal outbox:
  powershell -ExecutionPolicy Bypass -File C:\Users\sirok\MoCKA\infield\ai_save\phase2\seal_outbox.ps1
3) checkpoint:
  read LAST_CHAIN_HASH and store into:
  C:\Users\sirok\MoCKA\infield\ai_save\phase2\state.json (last_chain_hash)

NOTE: Current chain hash (checkpoint example)
fc33b5f36e4700b812522659599c6559c726b7357d55b4ac8dc08c592be2e70d


NOTE: Phase2 one-shot runner (canonical)
- Run:
  powershell -ExecutionPolicy Bypass -File C:\Users\sirok\MoCKA\infield\ai_save\phase2\run_phase2.ps1
- Behavior:
  - If no new lines in index.csv: prints 'OK: no new packets; skip seal' and exits
  - If new lines exist: emits sync_*.jsonl, seals outbox, updates checkpoint (state.json)

NOTE: State files
- Diff cursor:
  C:\Users\sirok\MoCKA\infield\ai_save\phase2\diff_state.json
- Seal checkpoint:
  C:\Users\sirok\MoCKA\infield\ai_save\phase2\state.json




