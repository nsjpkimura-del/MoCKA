import hashlib
import json
import re
import subprocess
from pathlib import Path

HEX64_RE = re.compile(r"^[0-9a-fA-F]{64}$")

EXCLUDE_PATHS = {
    "mocka-governance-kernel/anchors/anchor_record.json",
}

def run_bytes(cmd: list[str]) -> bytes:
    p = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise SystemExit(
            "ERROR: command failed: " + " ".join(cmd) + "\n" +
            "stdout:\n" + (p.stdout.decode("utf-8", errors="replace")) + "\n" +
            "stderr:\n" + (p.stderr.decode("utf-8", errors="replace"))
        )
    return p.stdout

def run_text(cmd: list[str]) -> str:
    return run_bytes(cmd).decode("utf-8", errors="replace")

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def extract_commit_hash_from_external_ref(external_ref: str) -> str:
    m = re.search(r"/commit/([0-9a-fA-F]{7,40})", external_ref)
    if not m:
        raise SystemExit("ERROR: external_ref must contain /commit/<hash>")
    return m.group(1).lower()

def load_anchor_record(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"ERROR: anchor_record not found: {path}")
    text = path.read_text(encoding="utf-8-sig")
    return json.loads(text)

def git_ls_tree_paths(commit: str) -> list[str]:
    out = run_bytes(["git", "ls-tree", "-r", "-z", "--name-only", commit])
    parts = out.split(b"\x00")
    paths = []
    for b in parts:
        if not b:
            continue
        p = b.decode("utf-8", errors="strict")
        p = p.replace("\\", "/")
        paths.append(p)
    return paths

def git_show_blob(commit: str, path: str) -> bytes:
    spec = f"{commit}:{path}"
    return run_bytes(["git", "show", spec])

def main() -> int:
    anchor_path = Path("mocka-governance-kernel/anchors/anchor_record.json")
    ar = load_anchor_record(anchor_path)

    expected = str(ar.get("sealed_summary_hash", "")).lower()
    if not HEX64_RE.match(expected):
        raise SystemExit("ERROR: sealed_summary_hash in anchor_record must be 64-hex")

    semantics = ar.get("external_ref_semantics", "")
    if semantics != "sealing_commit_reference":
        raise SystemExit("ERROR: external_ref_semantics must be sealing_commit_reference")

    spec_ver = str(ar.get("summary_hash_spec_version", ""))
    if spec_ver != "1.0":
        raise SystemExit("ERROR: summary_hash_spec_version must be 1.0")

    sealing_commit = extract_commit_hash_from_external_ref(ar.get("external_ref", ""))

    # enumerate tracked files in the sealing commit tree (no filesystem walking)
    paths = git_ls_tree_paths(sealing_commit)

    # apply normative exclusions
    paths = [p for p in paths if p not in EXCLUDE_PATHS]

    # lexicographic order by repo-relative forward-slash path
    paths.sort()

    records = bytearray()
    for p in paths:
        blob = git_show_blob(sealing_commit, p)
        blob_hash = hashlib.sha256(blob).hexdigest().encode("ascii")
        records += p.encode("utf-8")
        records += b"\x00"
        records += blob_hash
        records += b"\x0A"

    sealed = hashlib.sha256(records).hexdigest().lower()

    print("sealed_summary_hash: " + sealed)
    print("sealing_commit: " + sealing_commit)

    if sealed != expected:
        raise SystemExit(
            "ERROR: sealed_summary_hash mismatch\n" +
            "computed: " + sealed + "\n" +
            "expected: " + expected + "\n" +
            "note: anchor_record.json points to the sealing commit; update anchor_record only if the sealing commit changes"
        )

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
