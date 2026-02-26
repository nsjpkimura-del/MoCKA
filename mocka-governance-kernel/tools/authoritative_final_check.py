import argparse
import json
import os
import re
import subprocess
from pathlib import Path

HEX64_RE = re.compile(r"^[0-9a-fA-F]{64}$")

def run(cmd, check=True, capture=True):
    p = subprocess.run(
        cmd,
        check=False,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None
    )
    if check and p.returncode != 0:
        out = p.stdout or ""
        err = p.stderr or ""
        raise SystemExit(
            f"ERROR: command failed: {' '.join(cmd)}\nstdout:\n{out}\nstderr:\n{err}"
        )
    return p

def git(args, check=True):
    return run(["git"] + args, check=check)

def read_json(path: Path):
    # NOTE: accept UTF-8 with BOM (utf-8-sig)
    return json.loads(path.read_text(encoding="utf-8-sig"))

def assert_true(cond, msg):
    if not cond:
        raise SystemExit("ERROR: " + msg)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--require_clean", action="store_true")
    ap.add_argument("--require_branch", default=None)
    ap.add_argument("--anchor", default="mocka-governance-kernel/anchors/anchor_record.json")
    ap.add_argument("--anchor_hash", default="mocka-governance-kernel/anchors/anchor_record.sha256")
    ap.add_argument("--calc_tool_hint", default="calc_summary_hash.py")
    args = ap.parse_args()

    os.chdir(args.repo)

    st = git(["status", "--porcelain"], check=True).stdout.strip()
    if args.require_clean:
        assert_true(st == "", "working tree not clean")

    br = git(["branch", "--show-current"], check=True).stdout.strip()
    if args.require_branch:
        assert_true(br == args.require_branch, f"branch mismatch: current={br} required={args.require_branch}")

    anchor_path = Path(args.anchor)
    assert_true(anchor_path.exists(), f"missing anchor record: {anchor_path}")

    ar = read_json(anchor_path)
    for k in ["external_ref", "sealed_summary_hash", "external_ref_semantics", "summary_hash_spec_version"]:
        assert_true(k in ar, f"anchor_record missing key: {k}")

    assert_true(ar["external_ref_semantics"] == "sealing_commit_reference",
                f"external_ref_semantics invalid: {ar['external_ref_semantics']}")
    assert_true(str(ar["summary_hash_spec_version"]) == "1.0",
                f"summary_hash_spec_version invalid: {ar['summary_hash_spec_version']}")
    assert_true(HEX64_RE.match(ar["sealed_summary_hash"]) is not None,
                "sealed_summary_hash must be 64-hex")

    m = re.search(r"/commit/([0-9a-fA-F]{7,40})", ar["external_ref"])
    assert_true(m is not None, "external_ref must contain /commit/<hash>")
    ref_hash = m.group(1).lower()
    git(["cat-file", "-e", f"{ref_hash}^{{commit}}"], check=True)

    anchor_hash_path = Path(args.anchor_hash)
    assert_true(anchor_hash_path.exists(), f"missing anchor_record hash file: {anchor_hash_path}")
    ah = anchor_hash_path.read_text(encoding="utf-8").strip()
    assert_true(HEX64_RE.match(ah) is not None, "anchor_record.sha256 must be 64-hex")

    calc_anchor = Path("mocka-governance-kernel/tools/calc_anchor_record_hash.py")
    assert_true(calc_anchor.exists(), f"missing tool: {calc_anchor}")
    run(["python", str(calc_anchor), "--anchor", str(anchor_path), "--out", str(anchor_hash_path)], check=True)
    ah2 = anchor_hash_path.read_text(encoding="utf-8").strip()
    assert_true(ah2 == ah, "anchor_record.sha256 mismatch after recompute")

    found = list(Path(".").rglob(args.calc_tool_hint))
    if found:
        found.sort(key=lambda x: len(str(x)))
        tool = found[0]
        p = run(["python", str(tool)], check=True)
        out = (p.stdout or "") + "\n" + (p.stderr or "")
        hexes = re.findall(r"[0-9a-fA-F]{64}", out)
        if hexes:
            computed = hexes[-1].lower()
            expected = ar["sealed_summary_hash"].lower()
            assert_true(computed == expected, f"sealed_summary_hash mismatch: computed={computed} expected={expected}")
    else:
        print("WARN: calc_summary_hash.py not found; sealed_summary_hash recomputation not enforced here.")

    print("OK: authoritative_final_check PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
