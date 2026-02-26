from __future__ import annotations
import shutil
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / "governance" / "_chaos_tmp"

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def fail(msg: str):
    print("FAIL:", msg)
    sys.exit(1)

def main() -> int:
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True)

    # registry 改竄テスト
    regs = list(ROOT.glob("**/*registry*.json"))
    if not regs:
        fail("registry not found")
    reg = regs[0]
    tampered = TMP / "registry_tampered.json"
    shutil.copy2(reg, tampered)
    tampered.write_text(tampered.read_text() + "\n ", encoding="utf-8")

    if sha256_file(reg) == sha256_file(tampered):
        fail("registry tamper not detected (hash identical)")

    print("PASS: registry tamper detectable")

    # governance_event hash mismatch テスト
    gov = ROOT / "governance" / "governance_event.json"
    if gov.exists():
        original = gov.read_text(encoding="utf-8")
        gov.write_text(original + " ", encoding="utf-8")
        if sha256_file(gov) == hashlib.sha256(original.encode()).hexdigest():
            fail("governance_event tamper not detectable")
        gov.write_text(original, encoding="utf-8")
        print("PASS: governance_event tamper detectable")

    print("PASS: chaos basic checks")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
