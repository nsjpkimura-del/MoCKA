from __future__ import annotations
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXCLUDE_PATHS = {
    "governance/anchor_record.json",  # 自己参照防止（アンカーは制度外）
}

EXCLUDE_DIRS = {".git", "__pycache__"}
EXCLUDE_SUFFIXES = {".private.pem"}  # 秘密鍵は制度外

def should_include(p: Path) -> bool:
    if not p.is_file():
        return False

    rel = p.relative_to(ROOT).as_posix()

    if rel in EXCLUDE_PATHS:
        return False

    if any(part in EXCLUDE_DIRS for part in p.parts):
        return False

    if any(p.name.endswith(suf) for suf in EXCLUDE_SUFFIXES):
        return False

    return True

def main() -> int:
    h = hashlib.sha256()

    files = sorted(
        [p for p in ROOT.rglob("*") if should_include(p)],
        key=lambda x: x.relative_to(ROOT).as_posix()
    )

    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        h.update(rel.encode("utf-8"))
        h.update(b"\n")
        h.update(p.read_bytes())
        h.update(b"\n")

    print(h.hexdigest())
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
