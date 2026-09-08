@echo off
setlocal enabledelayedexpansion

title wrld.v2 - Local Persistent AI Society

:: Resolve script root directory
cd /d "%~dp0"
set "PROJECT_DIR=%~dp0"

echo ==================================================
echo Starting wrld.v2...
echo ==================================================

:: 1. Check if local .venv already exists and has a valid Python
set "VENV_PYTHON=%PROJECT_DIR%.venv\Scripts\python.exe"

if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" -c "import sys, tkinter; sys.exit(0 if (3, 10) <= sys.version_info < (3, 13) else 1)" >nul 2>nul
    if !ERRORLEVEL! EQU 0 (
        echo Using existing local virtual environment .venv...
        goto RUN_BOOTSTRAP
    )
)

:: 2. Check if local bootstrapped runtime exists and is valid
set "BOOTSTRAP_PYTHON=%PROJECT_DIR%runtime\python312\python.exe"

if exist "%BOOTSTRAP_PYTHON%" (
    "%BOOTSTRAP_PYTHON%" -c "import sys, tkinter; sys.exit(0 if (3, 10) <= sys.version_info < (3, 13) else 1)" >nul 2>nul
    if !ERRORLEVEL! EQU 0 (
        echo Using existing bootstrapped Python runtime in runtime\python312...
        set "VENV_PYTHON=%BOOTSTRAP_PYTHON%"
        goto RUN_BOOTSTRAP
    )
)

:: 3. Search for installed supported Python on system PATH (3.12, 3.11, 3.10)
set "FOUND_PYTHON="

call :TRY_PY_LAUNCHER 3.12
if defined FOUND_PYTHON goto CREATE_VENV

call :TRY_PY_LAUNCHER 3.11
if defined FOUND_PYTHON goto CREATE_VENV

call :TRY_PY_LAUNCHER 3.10
if defined FOUND_PYTHON goto CREATE_VENV

call :TRY_EXEC python3.12
if defined FOUND_PYTHON goto CREATE_VENV

call :TRY_EXEC python3.11
if defined FOUND_PYTHON goto CREATE_VENV

call :TRY_EXEC python3.10
if defined FOUND_PYTHON goto CREATE_VENV

call :TRY_EXEC python
if defined FOUND_PYTHON goto CREATE_VENV

:: 4. If no supported Python is found on system PATH, launch.py will automatically download official Python 3.12
echo No supported Python found on system PATH. launch.py will automatically download Python 3.12...
set "VENV_PYTHON=python"
goto RUN_BOOTSTRAP

:CREATE_VENV
echo Found supported Python interpreter: !FOUND_PYTHON!
echo Creating local virtual environment in "%PROJECT_DIR%.venv"...

!FOUND_PYTHON! -m venv "%PROJECT_DIR%.venv" >nul 2>nul
if !ERRORLEVEL! EQU 0 (
    set "VENV_PYTHON=%PROJECT_DIR%.venv\Scripts\python.exe"
) else (
    set "VENV_PYTHON=python"
)

:RUN_BOOTSTRAP

:: Run launch.py to verify environment, download Python 3.12 if missing, verify dependencies and model
"%VENV_PYTHON%" launch.py
if !ERRORLEVEL! NEQ 0 (
    echo ERROR: Environment verification failed.
    pause
    exit /b 1
)

:: Run main simulation application using verified .venv python or bootstrapped runtime
if exist "%PROJECT_DIR%.venv\Scripts\python.exe" (
    set "EXEC_PYTHON=%PROJECT_DIR%.venv\Scripts\python.exe"
) else if exist "%PROJECT_DIR%runtime\python312\python.exe" (
    set "EXEC_PYTHON=%PROJECT_DIR%runtime\python312\python.exe"
) else (
    set "EXEC_PYTHON=python"
)

"%EXEC_PYTHON%" main.py
if !ERRORLEVEL! NEQ 0 (
    echo ERROR: wrld.v2 exited with an error.
    pause
    exit /b 1
)

pause
exit /b 0

:TRY_PY_LAUNCHER
py -%1 -c "import sys, tkinter; sys.exit(0 if (3, 10) <= sys.version_info < (3, 13) else 1)" >nul 2>nul
if !ERRORLEVEL! EQU 0 (
    set "FOUND_PYTHON=py -%1"
)
exit /b 0

:TRY_EXEC
where %1 >nul 2>nul
if !ERRORLEVEL! NEQ 0 exit /b 0
%1 -c "import sys, tkinter; sys.exit(0 if (3, 10) <= sys.version_info < (3, 13) else 1)" >nul 2>nul
if !ERRORLEVEL! EQU 0 (
    set "FOUND_PYTHON=%1"
)
exit /b 0
