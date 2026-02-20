MoCKA Phase12 Verify Pack

Purpose
- Third-party verification of Proof-Grade Audit (chain + signature).

Included
- audit\ed25519\audit.db
- audit\ed25519\keys\ed25519_public.key
- config\phase12_audit_canonical.json
- verify_full_chain.py
- verify_full_chain_and_signature.py
- verify.bat
- manifest.sha256.txt

How to verify (Windows)
1) Extract zip anywhere
2) Run verify.bat

Expected outputs
- verify_full_chain.py: status OK
- verify_full_chain_and_signature.py: status OK, signature_checked >= 1
- If any mismatch exists, the script exits with non-zero code.

Notes
- This pack is designed to be self-contained.
- Python must be available. Recommended: use the same venv Python path shown in verify.bat (edit if needed).