@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if not errorlevel 1 (
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
    if errorlevel 1 goto no_python
    py -3 memory_manager.py
    goto finished
)

where python >nul 2>&1
if errorlevel 1 goto no_python
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 goto no_python
python memory_manager.py
goto finished

:no_python
echo Python 3.10 or newer is required. Install Python, then run this launcher again.
echo The Python installer is available from https://www.python.org/downloads/windows/
pause
exit /b 1

:finished
if errorlevel 1 (
    echo The memory service exited with an error.
    pause
    exit /b 1
)
endlocal
