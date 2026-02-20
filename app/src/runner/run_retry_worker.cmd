@echo off
setlocal
cd /d C:\Users\sirok\MoCKA\app\src

set "PYTHONPATH=C:\Users\sirok\MoCKA\app\src"
set "MOCKA_HOME=C:\Users\sirok\MoCKA"
set "MOCKA_INFIELD=C:\Users\sirok\MoCKA\infield"
set "MOCKA_DB=C:\Users\sirok\MoCKA\infield\state\mocka_state.db"

echo UTC=%DATE% %TIME%>>"C:\Users\sirok\MoCKA\infield\logs\runner_out.log"
echo CWD=%CD%>>"C:\Users\sirok\MoCKA\infield\logs\runner_out.log"
echo PYTHONPATH=%PYTHONPATH%>>"C:\Users\sirok\MoCKA\infield\logs\runner_out.log"

"C:\Users\sirok\MoCKA\app\.venv311\Scripts\python.exe" "C:\Users\sirok\MoCKA\app\src\runner\retry_worker_runner.py" 1>>"C:\Users\sirok\MoCKA\infield\logs\runner_out.log" 2>>"C:\Users\sirok\MoCKA\infield\logs\runner_error.log"
exit /b %errorlevel%
