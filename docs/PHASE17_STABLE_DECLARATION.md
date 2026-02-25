PHASE17 STABLE DECLARATION

1\. Scope



This document declares MoCKA Phase17 as STABLE with determinism and strict verification guarantees.



2\. Guarantees



Deterministic summary generation



The acceptance summary\_matrix.json is deterministically rebuilt from freeze\_manifest v2 verify\_packs.



A stable summary\_hash is produced and verified.



Strict manifest enforcement



verify\_packs\[\*].path must resolve to an existing file.



Non-file paths cause STRICT\_MANIFEST\_FAIL.



Encoding tolerance



JSON inputs are loaded with utf-8-sig to tolerate BOM safely.



CI enforcement



GitHub Actions runs determinism checks on push to main and pull requests.



3\. Entry Points



Verification: python verify/verify\_all.py



Determinism check: python tools/phase17\_determinism\_check.py



4\. Artifacts Policy



Runtime/generated artifacts (db, summary, state files) are not tracked in git.



Only code, docs, and deterministic verification logic are tracked.



5\. Tag

The stable tag must point to the commit that satisfies all guarantees above.

