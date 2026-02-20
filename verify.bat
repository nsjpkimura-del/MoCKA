@echo off
setlocal enabledelayedexpansion

REM Use venv python if present next to this pack (recommended).
REM Fallback to "python" in PATH.

set PY=.\venv\Scripts\python.exe
if exist "%PY%" goto RUN

set PY=python

:RUN
echo [1/2] verify_full_chain.py
"%PY%" ".\verify_full_chain.py"
if errorlevel 1 (
  echo FAIL: verify_full_chain.py
  exit /b 1
)

echo [2/2] verify_full_chain_and_signature.py
"%PY%" ".\verify_full_chain_and_signature.py"
if errorlevel 1 (
  echo FAIL: verify_full_chain_and_signature.py
  exit /b 1
)

echo OK: CHAIN_OK + SIGNATURE_OK
exit /b 0