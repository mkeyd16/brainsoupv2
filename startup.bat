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

:: Check if local .venv already exists and has a supported Python
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

:: Try Windows Python Launcher (py -3.12, py -3.11, py -3.10)
for %%V in (3.12 3.11 3.10) do (
    if not defined FOUND_PYTHON (
        py -%%V -c "import sys; print(sys.executable)" >nul 2>nul
        if !ERRORLEVEL! EQU 0 (
            set "FOUND_PYTHON=py -%%V"
        )
    )
)

:: Try python executables in PATH if py launcher not found
if not defined FOUND_PYTHON (
    for %%P in (python3.12 python3.11 python3.10 python) do (
        if not defined FOUND_PYTHON (
            where %%P >nul 2>nul
            if !ERRORLEVEL! EQU 0 (
                %%P -c "import sys; sys.exit(0 if (3, 10) <= sys.version_info < (3, 13) else 1)" >nul 2>nul
                if !ERRORLEVEL! EQU 0 (
                    set "FOUND_PYTHON=%%P"
                )
            )
        )
    )
)

if not defined FOUND_PYTHON (
    echo ==================================================
    echo ERROR: No supported Python version (3.10, 3.11, or 3.12) was found on your system.
    echo wrld.v2 requires Python 3.10, 3.11, or 3.12 to use prebuilt llama-cpp-python wheels.
    echo.
    echo Python 3.13+ lacks prebuilt llama-cpp-python binary wheels, requiring C++/CMake build toolchains.
    echo Please install Python 3.10, 3.11, or 3.12 from https://www.python.org/downloads/
    echo and ensure "Add Python to PATH" is checked during installation.
    echo ==================================================
    pause
    exit /b 1
)

echo Found supported Python interpreter: %FOUND_PYTHON%
echo Creating local virtual environment .venv...

%FOUND_PYTHON% -m venv "%PROJECT_DIR%.venv"
if !ERRORLEVEL! NEQ 0 (
    echo ERROR: Failed to create virtual environment in "%PROJECT_DIR%.venv".
    pause
    exit /b 1
)

set "VENV_PYTHON=%PROJECT_DIR%.venv\Scripts\python.exe"

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

pause
