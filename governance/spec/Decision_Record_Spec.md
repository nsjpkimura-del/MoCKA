# Decision Record Spec v1.0

## 1. Definition
Long-term memory is an externalized, auditable record of important decisions extracted from conversations.
The minimal unit is a Decision Unit. One Decision Unit maps to exactly one EventId and one Canonical record.

## 2. Three-Layer Model
### 2.1 Index Layer
- governance/history_index.csv
Rules: one row per decision; no multiline cells; append-only.

### 2.2 Canonical Layer
- governance/history/REC-YYMMDD-SERIAL.md
Rules: one file per decision; YAML front matter; content hash; store with index in same git commit when possible.

### 2.3 Propagation Layer
Reduced public summary for outfield systems.
Rules: only Importance A/B; fixed public fields; human approval required.

## 3. EventType (fixed)
- POLICY_CHANGE
- ARCH_DECISION
- EXTERNAL_DEP
- PARADIGM_SHIFT
- INCIDENT_RESOLUTION
- META_GOV

## 4. Importance (fixed)
A: institution-level
B: operational-level
C: reference-level (not propagated)

## 5. Index CSV Schema (fixed order)
event_id,date,event_type,title_20,summary_100,importance,canonical_path,content_hash,status

Constraints:
- title_20 <= 20 chars, single-line
- summary_100 <= 100 chars, single-line
- date = YYYY-MM-DD
Status: Draft / Active / Deprecated

## 6. Canonical Markdown Schema
YAML keys required:
event_id,date,event_type,importance,status,title,summary,related_events,attachments,hash.algorithm,hash.value,hash.git_commit,hash.ots_proof

Body sections required:
Context, Options, Decision, Rationale, Impact, Implementation, Revalidation

## 7. Hashing Rule
Compute sha256 over the canonical content where hash.value is empty string, then fill hash.value with the digest.

## 8. Deprecation Rule
Do not rewrite past decisions. Create a new decision to supersede. Mark old as Deprecated.