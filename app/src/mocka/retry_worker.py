import os
import sys

def _enforce_entrypoint_mark() -> None:
    mark = os.getenv("MOCKA_ENTRYPOINT", "")
    if mark != "run_infield_retry_worker.cmd":
        sys.stderr.write("entrypoint missing: use run_infield_retry_worker.cmd\n")
        raise SystemExit(2)

import sys
import os
import traceback
from datetime import datetime
from contextlib import redirect_stdout, redirect_stderr
import runpy

# ------------------------------------------------------------
# パス設定（MoCKA 運用のための明示的 sys.path 制御）
# ------------------------------------------------------------

# このファイル: C:\Users\sirok\mocka-infield\tools\retry_worker_with_log.py
THIS_FILE = os.path.abspath(__file__)
TOOLS_DIR = os.path.dirname(THIS_FILE)                     # ...\mocka-infield\tools
PROJECT_ROOT_INFIELD = os.path.dirname(TOOLS_DIR)          # ...\mocka-infield

# replan_bridge_auto.py の実体があるディレクトリ
PROJECT_ROOT_PYTHONBRIDGE = r"C:\Users\sirok\mocka-pythonbridge"

# sys.path に追加（先頭優先）
for p in [PROJECT_ROOT_INFIELD, PROJECT_ROOT_PYTHONBRIDGE]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ------------------------------------------------------------
# ログ設定
# ------------------------------------------------------------

LOG_DIR = os.path.join(TOOLS_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, "retry_worker.log")

# 実行対象スクリプト
RETRY_WORKER_SCRIPT = os.path.join(TOOLS_DIR, "retry_worker_runner.py")


def log_line(f, message: str) -> None:
    """ログにタイムスタンプ付きで1行書き込む"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    f.write(f"[{now}] {message}\n")
    f.flush()


def main() -> int:
    """retry_worker_runner.py を実行し、ログにすべて記録する"""
    with open(LOG_PATH, "a", encoding="utf-8") as log_file, \
            redirect_stdout(log_file), \
            redirect_stderr(log_file):

        log_line(log_file, "START: retry_worker_with_log")

        try:
            # runner の存在確認
            if not os.path.exists(RETRY_WORKER_SCRIPT):
                log_line(log_file, f"ERROR: retry_worker_runner.py not found at {RETRY_WORKER_SCRIPT}")
                log_line(log_file, "END: failure (missing retry_worker_runner.py)")
                return 1

            # 実行環境情報
            log_line(log_file, f"INFO: Python executable: {sys.executable}")
            log_line(log_file, f"INFO: Running script: {RETRY_WORKER_SCRIPT}")
            log_line(log_file, f"INFO: sys.path (top 5): {sys.path[:5]}")

            # retry_worker_runner.py を __main__ として実行
            runpy.run_path(RETRY_WORKER_SCRIPT, run_name="__main__")

            log_line(log_file, "END: success")
            return 0

        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
            log_line(log_file, f"SystemExit: code={code}")
            log_line(log_file, "END: failure (SystemExit)")
            return code

        except Exception:
            log
