@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "PYCMD=py -3"
) else (
    set "PYCMD=python"
)
if not exist ".venv\Scripts\python.exe" (
    %PYCMD% -m venv .venv
    if errorlevel 1 goto :error
)
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if errorlevel 1 goto :error
echo.
echo EMBERLINE 3.0 - LOCAL SYNTHETIC SANDBOX
echo Open http://127.0.0.1:8000 in your browser
echo Press Ctrl+C to stop.
echo.
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
exit /b 0
:error
echo Setup failed. Install Python 3.10+ and retry.
pause
exit /b 1
