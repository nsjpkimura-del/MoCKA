# Summary Hash Specification v1.0

## Scope
This document defines the normative algorithm for computing the MoCKA sealed_summary_hash.
The goal is reproducibility across machines and future re-implementations.

## Inputs
The summary hash is computed over a deterministic manifest of repository files under version control,
excluding explicitly excluded artifacts.

### Included set
All tracked files in the repository at the target commit, subject to Exclusions below.

### Exclusions (normative)
1. mocka-governance-kernel/anchors/anchor_record.json
   Rationale: avoid circular dependency and allow anchor record to reference sealing commit.
2. Any private keys or secrets excluded by .gitignore.
3. Any files outside the repository root.

### Anchor record tamper detection
Because anchor_record.json is excluded, its integrity MUST be covered via:
mocka-governance-kernel/anchors/anchor_record.sha256
This file is included in the summary hash and is updated by tools/calc_anchor_record_hash.py.
Any modification to anchor_record.json MUST be accompanied by updating anchor_record.sha256.

## Normalization rules (normative)
### File ordering
Files MUST be processed in lexicographic order of their repository-relative path using forward slashes.

### Path encoding
Paths MUST be treated as UTF-8 and normalized to forward slashes in the manifest.

### Content bytes
File content bytes MUST be read as raw bytes exactly as stored in the repository.
No newline normalization is permitted.

### Hash function
SHA-256 over a canonical concatenation of records:
For each file:
- path_utf8 + 0x00 + sha256(file_bytes) + 0x0A

The final sealed_summary_hash is SHA-256 of the concatenated records.

## Versioning
This specification is version 1.0.
Any incompatible change MUST bump summary_hash_spec_version.

## Security notes
This hash provides integrity (tamper evidence), not correctness or legitimacy guarantees.
