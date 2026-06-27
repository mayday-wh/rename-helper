@echo off
rem Use UTF-8 to avoid garbled text in cmd.
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

rem Run from this batch file's directory.
cd /d "%~dp0"

rem Project command.
set "APP_NAME=Rename"
set "TARGET_PY=main.py"
set "RUN_CMD=uv run --no-sync python %TARGET_PY%"

rem Basic validation mode for scripts and CI.
if /i "%~1"=="--check" (
    echo Checking %APP_NAME%...
    uv run --no-sync python -m py_compile %TARGET_PY%
    exit /b %errorlevel%
)

echo Starting %APP_NAME%...
echo %RUN_CMD%
echo.

%RUN_CMD%

set "EXIT_CODE=%errorlevel%"
echo.

if not "%EXIT_CODE%"=="0" (
    echo Run failed. Exit code: %EXIT_CODE%
) else (
    echo Run finished.
)

echo.
pause
exit /b %EXIT_CODE%
