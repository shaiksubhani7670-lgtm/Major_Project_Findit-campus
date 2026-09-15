@echo off
title FindIt Campus Smart Lost ^& Found Launcher
setlocal EnableDelayedExpansion

:: ─────────────────────────────────────────────
::  Resolve paths (works from any directory)
:: ─────────────────────────────────────────────
set "ROOT_DIR=%~dp0"
set "BACKEND_DIR=%ROOT_DIR%findit-campus\backend"
set "VENV_DIR=%BACKEND_DIR%\venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_PIP=%VENV_DIR%\Scripts\pip.exe"
set "REQ_FILE=%BACKEND_DIR%\requirements.txt"
set "PYTHON_EXE="

:: ─────────────────────────────────────────────
::  Step 1 — Find a working system Python
:: ─────────────────────────────────────────────
echo.
echo  [1/4] Locating Python...

:: Try py launcher first (most reliable on Windows)
py --version >nul 2>&1
if not errorlevel 1 ( set "PYTHON_EXE=py" & goto :python_found )

:: Try python in PATH
python --version >nul 2>&1
if not errorlevel 1 ( set "PYTHON_EXE=python" & goto :python_found )

:: Try python3 in PATH
python3 --version >nul 2>&1
if not errorlevel 1 ( set "PYTHON_EXE=python3" & goto :python_found )

:: Scan common install locations
for %%V in (314 313 312 311 310 39 38) do (
    if "!PYTHON_EXE!"=="" (
        if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
            set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
        )
        if exist "C:\Python%%V\python.exe" (
            if "!PYTHON_EXE!"=="" set "PYTHON_EXE=C:\Python%%V\python.exe"
        )
    )
)

if "!PYTHON_EXE!"=="" (
    echo.
    echo  [ERROR] Python was not found on this computer.
    echo  Please install Python 3.8+ from https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:python_found
echo         Found: !PYTHON_EXE!

:: ─────────────────────────────────────────────
::  Step 2 — Delete broken venv if python.exe fails
:: ─────────────────────────────────────────────
echo  [2/4] Checking virtual environment...

if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" --version >nul 2>&1
    if errorlevel 1 (
        echo         Broken venv detected. Removing...
        rmdir /s /q "%VENV_DIR%"
    )
)

:: ─────────────────────────────────────────────
::  Step 3 — Create venv if missing
:: ─────────────────────────────────────────────
if not exist "%VENV_PYTHON%" (
    echo         Creating new virtual environment...
    "!PYTHON_EXE!" -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo  [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo         Virtual environment created.
)

:: ─────────────────────────────────────────────
::  Step 4 — Install / update dependencies
::  (pip skips already-installed packages, so this is fast on repeat runs)
:: ─────────────────────────────────────────────
echo  [3/4] Verifying dependencies...
"%VENV_PYTHON%" -c "import flask_sqlalchemy" >nul 2>&1
if errorlevel 1 (
    echo         Packages missing or incomplete - installing now.
    echo         This may take a few minutes on first run...
    "%VENV_PIP%" install --upgrade pip --quiet
    "%VENV_PIP%" install -r "%REQ_FILE%"
    if errorlevel 1 (
        echo.
        echo  [ERROR] Dependency installation failed.
        echo  Check your internet connection and try again.
        pause
        exit /b 1
    )
    echo         All packages installed successfully!
) else (
    echo         All packages OK.
)

echo  [4/4] Ready!

:: ─────────────────────────────────────────────
::  Main Menu
:: ─────────────────────────────────────────────
:menu
cls
echo =====================================================================
echo           FindIt Campus Lost ^& Found System Launcher
echo =====================================================================
echo.
echo   [1] Start Application Server  (http://localhost:5000)
echo   [2] Import Excel Logins ^& Seed Database  (seed.py)
echo   [3] Exit
echo.
echo =====================================================================
set /p opt="Select an option (1-3): "

if "%opt%"=="1" goto start_server
if "%opt%"=="2" goto seed_db
if "%opt%"=="3" goto exit_launcher

echo  Invalid choice. Please select 1, 2, or 3.
pause
goto menu

:start_server
echo.
echo  Starting Flask Application Server...
start "FindIt Campus Server" cmd /k "cd /d "%BACKEND_DIR%" && "%VENV_PYTHON%" run.py"
echo.
echo =====================================================================
echo  Server launched!  Open browser at: http://localhost:5000
echo =====================================================================
echo.
pause
goto menu

:seed_db
echo.
echo  Running database seeding and Excel logins import...
pushd "%BACKEND_DIR%"
"%VENV_PYTHON%" seed.py
popd
echo.
echo  Seeding complete. Preloaded students and Excel credentials imported!
echo.
pause
goto menu

:exit_launcher
exit
