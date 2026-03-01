NOTE: Phase2 Public Verify (Public Layer)

Purpose
- The public repository publishes the "container" only.
- Runtime artifacts remain excluded.
- The chain ledger can be verified by signature when available in the runtime environment.

Signed Artifact (runtime)
- infield/ai_save/phase2/outbox.manifest.chain.csv
- Detached signature is generated next to it:
  infield/ai_save/phase2/outbox.manifest.chain.csv.asc

Verification (local)
- gpg --verify infield/ai_save/phase2/outbox.manifest.chain.csv.asc infield/ai_save/phase2/outbox.manifest.chain.csv

Policy
- Do not commit runtime outputs (outbox, index, items, decisions).
- Public Git must not contain runtime data.