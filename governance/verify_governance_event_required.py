from __future__ import annotations

import base64
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from cryptography.hazmat.primitives.asymmetric import ed25519

def b64u_decode(s: str) -> bytes:
    s = s.strip()
    pad = "=" * ((4 - (len(s) % 4)) % 4)
    return base64.urlsafe_b64decode(s + pad)

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_json(p: Path) -> Dict[str, Any]:
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception as e:
        raise RuntimeError(f"json read failed: {p} err={e}")

def is_registry_json(obj: Dict[str, Any]) -> bool:
    schema = obj.get("schema")
    return isinstance(schema, str) and schema.startswith("mocka.keys.ed25519.registry.v")

def find_registry_candidates(root: Path) -> List[Path]:
    candidates: List[Path] = []
    for pat in ("**/*registry*.json", "**/registry.json"):
        for p in root.glob(pat):
            if not p.is_file():
                continue
            try:
                obj = load_json(p)
            except Exception:
                continue
            if is_registry_json(obj):
                candidates.append(p)
    candidates.sort(key=lambda x: (0 if "governance" in str(x).lower() else 1, len(str(x))))
    return candidates

def validate_governance_event(ev: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errs: List[str] = []
    if ev.get("schema") != "mocka.governance.event.v1":
        errs.append("schema must be mocka.governance.event.v1")
    if ev.get("event_type") != "registry_update":
        errs.append("event_type must be registry_update")
    cc = ev.get("change_class")
    if cc not in ("minor", "major"):
        errs.append("change_class must be minor or major")

    for k in ("previous_registry_hash", "new_registry_hash", "timestamp_utc", "signature"):
        if k not in ev:
            errs.append(f"missing field: {k}")

    approvers = ev.get("approvers")
    if not isinstance(approvers, list):
        errs.append("approvers must be list")
    else:
        if cc == "major" and len(approvers) == 0:
            errs.append("major change requires approvers non-empty")
        for i, a in enumerate(approvers):
            if not isinstance(a, str) or not a.strip():
                errs.append(f"approvers[{i}] must be non-empty string")

    if "signature" in ev and (not isinstance(ev["signature"], str) or not ev["signature"].strip()):
        errs.append("signature must be non-empty string (real signature required)")

    return (len(errs) == 0, errs)

def main() -> int:
    root = Path(__file__).resolve().parents[1]
    gov_event_path = root / "governance" / "governance_event.json"
    if not gov_event_path.exists():
        print("FAIL: governance_event.json not found")
        print(f"expected: {gov_event_path}")
        return 2

    ev = load_json(gov_event_path)
    ok, errs = validate_governance_event(ev)
    if not ok:
        print("FAIL: governance_event.json schema validation failed")
        for e in errs:
            print(f"- {e}")
        return 3

    regs = find_registry_candidates(root)
    if not regs:
        print("FAIL: registry json not found (schema mocka.keys.ed25519.registry.v*)")
        return 4

    reg_path = regs[0]
    reg_hash = sha256_file(reg_path)

    nrh = ev.get("new_registry_hash", "")
    if isinstance(nrh, str) and nrh.strip() and nrh.lower() != reg_hash.lower():
        print("FAIL: new_registry_hash does not match current registry file sha256")
        print(f"registry_path: {reg_path}")
        print(f"registry_sha256: {reg_hash}")
        print(f"event_new_registry_hash: {nrh}")
        return 5

    # signature verify using root_key_v2 public key
    pub_path = root / "governance" / "keys" / "root_key_v2.ed25519.public.b64u"
    if not pub_path.exists():
        print("FAIL: root_key_v2 public key not found for verification")
        return 6

    pub_raw = b64u_decode(pub_path.read_text(encoding="utf-8-sig"))
    pub = ed25519.Ed25519PublicKey.from_public_bytes(pub_raw)

    sig_b = b64u_decode(ev["signature"])
    ev_copy = dict(ev)
    ev_copy["signature"] = ""

    msg = json.dumps(ev_copy, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    try:
        pub.verify(sig_b, msg)
    except Exception as e:
        print("FAIL: governance_event signature invalid")
        print(f"err={e}")
        return 7

    print("PASS: governance_event required + signature valid")
    print(f"registry_path: {reg_path}")
    print(f"registry_sha256: {reg_hash}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
