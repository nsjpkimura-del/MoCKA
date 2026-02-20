@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem =========================
rem Fixed Paths (NO omission)
rem =========================
set "CWD_ROOT=C:\Users\sirok\MoCKA\app\src"
set "PY_EXE=C:\Users\sirok\MoCKA\app\.venv311\Scripts\python.exe"
set "PYTHONPATH=C:\Users\sirok\MoCKA\app\src"
set "MOCKA_HOME=C:\Users\sirok\MoCKA"
set "MOCKA_INFIELD=C:\Users\sirok\MoCKA\infield"
set "MOCKA_DB=C:\Users\sirok\MoCKA\infield\state\mocka_state.db"
set "LOG_DIR=C:\Users\sirok\MoCKA\infield\logs"

rem =========================
rem Worker Tag (collision-resistant)
rem  - 32k range is too small, so use 2x RANDOM + time fragments
rem =========================
set "TAG=%RANDOM%%RANDOM%"
set "T=%TIME%"
set "T=%T::=%"
set "T=%T:.=%"
set "T=%T: =0%"
set "WORKER_TAG=%TAG%_%T%"

rem =========================
rem Logs (separate by tag)
rem =========================
set "OUT_LOG=%LOG_DIR%\runner_out.infield_%WORKER_TAG%.log"
set "ERR_LOG=%LOG_DIR%\runner_error.infield_%WORKER_TAG%.log"

rem =========================
rem Move to working directory
rem =========================
cd /d "%CWD_ROOT%"

rem =========================
rem Header (audit trace)
rem =========================
echo ===== TEST_MARK TAG=%WORKER_TAG% UTC=%DATE% %TIME% ROUTE=INFIELD CWD=%CD% =====>>"%OUT_LOG%"
echo PYTHONPATH=%PYTHONPATH%>>"%OUT_LOG%"
echo MOCKA_DB=%MOCKA_DB%>>"%OUT_LOG%"

rem =========================
rem Execute
rem =========================
"%PY_EXE%" "C:\Users\sirok\MoCKA\app\src\runner\retry_worker_runner.py" 1>>"%OUT_LOG%" 2>>"%ERR_LOG%"

rem =========================
rem Exitcode trace
rem =========================
set "EC=%ERRORLEVEL%"
echo EXITCODE=%EC% TAG=%WORKER_TAG% UTC=%DATE% %TIME%>>"%OUT_LOG%"
exit /b %EC%
