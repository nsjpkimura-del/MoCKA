import os
import sys

EXPECTED = "run_infield_retry_worker.cmd"
VAR = "MOCKA_ENTRYPOINT"
FIXED_MSG = "entrypoint missing: use run_infield_retry_worker.cmd"

def enforce() -> None:
    mark = os.getenv(VAR, "")
    if mark != EXPECTED:
        sys.stderr.write(FIXED_MSG + "\n")
        raise SystemExit(2)