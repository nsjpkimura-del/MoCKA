@echo off
setlocal
cd /d C:\Users\sirok\MoCKA\app\src

set "MOCKA_ROUTE=INFIELD"
if exist "C:\Users\sirok\MoCKA\infield\state\mocka_route.txt" (
  set /p MOCKA_ROUTE=<"C:\Users\sirok\MoCKA\infield\state\mocka_route.txt"
)

echo UTC=%DATE% %TIME% ROUTE=%MOCKA_ROUTE%>>"C:\Users\sirok\MoCKA\infield\logs\dispatch.log"

if /I "%MOCKA_ROUTE%"=="OUTFIELD" (
  call "C:\Users\sirok\MoCKA\app\src\runner\run_outfield_retry_worker.cmd"
  exit /b %errorlevel%
)

call "C:\Users\sirok\MoCKA\app\src\runner\run_infield_retry_worker.cmd"
exit /b %errorlevel%
