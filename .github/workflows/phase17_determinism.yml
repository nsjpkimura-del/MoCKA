# PHASE18 ENTRYPOINT

## 0. Current Stable Anchor
- stable tag: phase17-stable
- verified determinism: tools/phase17_determinism_check.py PASS

## 1. Canonical Entry Points
- verify: python verify/verify_all.py
- determinism: python tools/phase17_determinism_check.py

## 2. Phase18 Mission (choose one as primary)
A. Row-level signature (finance-grade)
B. Multi-environment acceptance automation (repro across OS/Python)
C. Multi-pack operational hardening (verify_packs real-world scaling)

## 3. Phase18 Start Rule
- Always keep Phase17 stable guarantees green.
- Any Phase18 change must preserve:
  - STRICT_MANIFEST enforcement
  - deterministic summary_hash
  - CI determinism job PASS

## 4. First Task (default)
- Implement B: multi-environment acceptance automation via CI matrix.
  - Windows + Ubuntu
  - Python 3.12 and 3.13
  - Run tools/phase17_determinism_check.py
