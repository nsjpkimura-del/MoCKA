import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    now_utc = datetime.now(timezone.utc).isoformat()
    payload = {
        "utc": now_utc,
        "cwd": os.getcwd(),
        "executable": sys.executable,
        "argv": sys.argv,
        "sys_path": sys.path,
        "env": {
            "MOCKA_HOME": os.environ.get("MOCKA_HOME"),
            "MOCKA_INFIELD": os.environ.get("MOCKA_INFIELD"),
            "MOCKA_DB": os.environ.get("MOCKA_DB"),
        },
    }

    log_dir = Path(r"C:\Users\sirok\MoCKA\infield\logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    out_path = log_dir / "env_probe.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
