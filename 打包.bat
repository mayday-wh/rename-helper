@echo off
setlocal

rem Use UTF-8 to avoid garbled text in cmd.
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

cd /d "%~dp0"

rem Project config.
set "APP_NAME=RenameHelper_v1.2"
set "DISPLAY_NAME=RenameHelper v1.2"
set "PACKAGE_NAME=rename"
set "ENTRY=main.py"
set "DIST_DIR=dist"
set "ICON_DIR=logo"
set "ICON="
set "ICON_OPTION="

rem Optional data file copied to dist if it exists. Leave empty to skip.
set "DATA_FILE="

rem Keep uv cache inside the project folder.
set "UV_CACHE_DIR=%~dp0.uv-build-cache"
set "UV_PYTHON_INSTALL_DIR=%~dp0.uv-python"

title Build %APP_NAME%

echo ======================================================
echo                 PyInstaller Build Tool
echo ======================================================
echo.

if not exist "%ENTRY%" (
    echo [ERROR] Entry file not found: %ENTRY%
    echo.
    pause
    exit /b 1
)

if /i "%~1"=="--check" (
    echo [INFO] App name: %APP_NAME%
    echo [INFO] Display name: %DISPLAY_NAME%
    echo [INFO] Package name: %PACKAGE_NAME%
    echo [INFO] Entry: %ENTRY%
    echo [INFO] Output dir: %DIST_DIR%
    echo [OK] Build config check passed.
    exit /b 0
)

if exist "%ICON_DIR%\" (
    for %%I in (%ICON_DIR%\*.ico) do (
        set "ICON=%%~fI"
        goto :ICON_FOUND
    )
)

echo [WARN] No .ico file found. Build will continue without icon.
goto :ICON_DONE

:ICON_FOUND
set "ICON_OPTION=--icon=%ICON%"
echo [INFO] Icon: %ICON%

:ICON_DONE
echo [INFO] App name: %APP_NAME%
echo [INFO] Display name: %DISPLAY_NAME%
echo [INFO] Package name: %PACKAGE_NAME%
echo [INFO] Entry: %ENTRY%
echo [INFO] Output dir: %DIST_DIR%

echo [INFO] Cleaning old build files...
if exist build rd /s /q build
if exist "%APP_NAME%.spec" del /q "%APP_NAME%.spec"

echo [INFO] Starting PyInstaller via uv...
echo.

uv run --with pyinstaller python -m PyInstaller --clean --noconsole --onefile %ICON_OPTION% --name "%APP_NAME%" --distpath "%DIST_DIR%" "%ENTRY%"

echo.
if %errorlevel% neq 0 (
    echo [ERROR] Build failed. Check the output above.
    echo.
    pause
    exit /b 1
)

if "%DATA_FILE%"=="" goto BUILD_DONE
if not exist "%DATA_FILE%" (
    echo [WARN] %DATA_FILE% not found. Skip copying data file.
    goto BUILD_DONE
)

copy /Y "%DATA_FILE%" "%DIST_DIR%\%DATA_FILE%" >nul
echo [INFO] Copied %DATA_FILE% to %DIST_DIR%.

:BUILD_DONE
echo [DONE] Build succeeded: %DIST_DIR%\%APP_NAME%.exe
echo.
pause
