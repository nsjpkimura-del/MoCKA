# outbox_watch_ingest.py
# ASCII only. Polling watcher, no external deps.

from __future__ import annotations

import argparse
import os
import sys
import time
import subprocess
from typing import List, Optional


def list_targets(outbox_dir: str) -> List[str]:
    try:
        names = os.listdir(outbox_dir)
    except FileNotFoundError:
        return []
    files: List[str] = []
    for n in names:
        if n.startswith("file_edit_") and n.endswith(".json"):
            files.append(n)
        elif n.startswith("file_restore_") and n.endswith(".json"):
            files.append(n)
    files.sort()
    return [os.path.join(outbox_dir, n) for n in files]


def is_stable_file(path: str, settle_ms: int) -> bool:
    # Simple settle: size must be stable across two stats
    try:
        st1 = os.stat(path)
    except FileNotFoundError:
        return False
    time.sleep(max(0.0, settle_ms / 1000.0))
    try:
        st2 = os.stat(path)
    except FileNotFoundError:
        return False
    return st1.st_size == st2.st_size and st2.st_size > 0


def run_ingest(py: str, ingest: str, db: str, outbox: str, file_path: str) -> int:
    cmd = [py, ingest, "--db", db, "--outbox", outbox, "--file", file_path]
    # Inherit console I/O so it never blocks on PIPE
    p = subprocess.run(cmd)
    return int(p.returncode)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--python", default=None, help="python executable (default: current)")
    ap.add_argument("--ingest", required=True, help="path to ingest_outbox.py")
    ap.add_argument("--db", required=True, help="path to knowledge.db")
    ap.add_argument("--outbox", required=True, help="outbox directory")
    ap.add_argument("--poll-ms", type=int, default=750, help="poll interval ms")
    ap.add_argument("--settle-ms", type=int, default=80, help="file settle ms before ingest")
    ap.add_argument("--once", action="store_true", help="process current files once then exit")
    args = ap.parse_args(argv)

    py = args.python or sys.executable
    ingest = os.path.abspath(args.ingest)
    db = os.path.abspath(args.db)
    outbox = os.path.abspath(args.outbox)

    poll_s = max(0.1, args.poll_ms / 1000.0)

    seen = set()

    print(f"[watch] start outbox={outbox} db={db} poll_ms={args.poll_ms}")
    try:
        while True:
            targets = list_targets(outbox)
            for f in targets:
                f_abs = os.path.abspath(f)
                if f_abs in seen:
                    continue
                if not is_stable_file(f_abs, args.settle_ms):
                    continue

                rc = run_ingest(py, ingest, db, outbox, f_abs)
                if rc == 0:
                    seen.add(f_abs)
                else:
                    # retry later
                    pass

            if args.once:
                break

            time.sleep(poll_s)
    except KeyboardInterrupt:
        print("[watch] stopped by KeyboardInterrupt")
        return 130

    print("[watch] done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())