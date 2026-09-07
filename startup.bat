@echo off
setlocal enabledelayedexpansion

title wrld.v2 - Local Persistent AI Society

:: Resolve script root directory
cd /d "%~dp0"
set "PROJECT_DIR=%~dp0"

echo ==================================================
echo Starting wrld.v2...
echo ==================================================

:: Set virtual environment python path
set "VENV_PYTHON=%PROJECT_DIR%.venv\Scripts\python.exe"

:: Check if local .venv already exists and has a supported Python (3.10 - 3.12)
if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" -c "import sys; sys.exit(0 if (3, 10) <= sys.version_info < (3, 13) else 1)" >nul 2>nul
    if !ERRORLEVEL! EQU 0 (
        echo Using existing local virtual environment .venv...
        goto RUN_SIMULATION
    ) else (
        echo Existing .venv uses an unsupported Python version. Re-creating .venv...
    )
)

echo Searching for installed supported Python (3.10, 3.11, or 3.12)...
set "FOUND_PYTHON="

:: Check Windows Python Launcher (py -3.12, py -3.11, py -3.10)
call :TRY_PY_LAUNCHER 3.12
if defined FOUND_PYTHON goto CREATE_VENV

call :TRY_PY_LAUNCHER 3.11
if defined FOUND_PYTHON goto CREATE_VENV

call :TRY_PY_LAUNCHER 3.10
if defined FOUND_PYTHON goto CREATE_VENV

:: Check executables in PATH (python3.12, python3.11, python3.10, python)
call :TRY_EXEC python3.12
if defined FOUND_PYTHON goto CREATE_VENV

call :TRY_EXEC python3.11
if defined FOUND_PYTHON goto CREATE_VENV

call :TRY_EXEC python3.10
if defined FOUND_PYTHON goto CREATE_VENV

call :TRY_EXEC python
if defined FOUND_PYTHON goto CREATE_VENV

:: If no supported Python is found
echo ==================================================
echo ERROR: No supported Python installation was found.
echo.
echo wrld.v2 requires Python 3.10, 3.11, or 3.12
echo for the current prebuilt llama-cpp-python installation.
echo.
echo Detected Python versions are unsupported (e.g. Python 3.13+ or 3.9-).
echo Python 3.13+ lacks prebuilt binary wheels for llama-cpp-python.
echo.
echo No C++/CMake build toolchain will be installed automatically.
echo Please install Python 3.10, 3.11, or 3.12 from https://www.python.org/downloads/
echo and ensure "Add Python to PATH" is checked during installation.
echo ==================================================
pause
exit /b 1

:TRY_PY_LAUNCHER
py -%1 -c "import sys; sys.exit(0 if (3, 10) <= sys.version_info < (3, 13) else 1)" >nul 2>nul
if !ERRORLEVEL! EQU 0 (
    set "FOUND_PYTHON=py -%1"
)
exit /b 0

:TRY_EXEC
where %1 >nul 2>nul
if !ERRORLEVEL! NEQ 0 exit /b 0
%1 -c "import sys; sys.exit(0 if (3, 10) <= sys.version_info < (3, 13) else 1)" >nul 2>nul
if !ERRORLEVEL! EQU 0 (
    set "FOUND_PYTHON=%1"
)
exit /b 0

:CREATE_VENV
echo Found supported Python interpreter: !FOUND_PYTHON!
echo Creating local virtual environment in "%PROJECT_DIR%.venv"...

!FOUND_PYTHON! -m venv "%PROJECT_DIR%.venv"
if !ERRORLEVEL! NEQ 0 (
    echo ERROR: Failed to create virtual environment in "%PROJECT_DIR%.venv".
    pause
    exit /b 1
)

set "VENV_PYTHON=%PROJECT_DIR%.venv\Scripts\python.exe"

:: Verify newly created .venv Python version
"%VENV_PYTHON%" -c "import sys; sys.exit(0 if (3, 10) <= sys.version_info < (3, 13) else 1)" >nul 2>nul
if !ERRORLEVEL! NEQ 0 (
    echo ==================================================
    echo ERROR: The created .venv uses an unsupported Python version.
    echo wrld.v2 requires Python 3.10, 3.11, or 3.12.
    echo ==================================================
    pause
    exit /b 1
)

:RUN_SIMULATION

:: Run launch.py to verify dependencies and model file
"%VENV_PYTHON%" launch.py
if !ERRORLEVEL! NEQ 0 (
    echo ERROR: Environment verification failed.
    pause
    exit /b 1
)

:: Run main simulation application
"%VENV_PYTHON%" main.py
if !ERRORLEVEL! NEQ 0 (
    echo ERROR: wrld.v2 exited with an error.
    pause
    exit /b 1
)

pause
