@echo off
setlocal enabledelayedexpansion

title wrld.v2 - Local Persistent AI Society

echo ==================================================
echo Starting wrld.v2...
echo ==================================================

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.10+ and ensure "Add Python to PATH" is checked.
    pause
    exit /b 1
)

python launch.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Environment verification failed.
    pause
    exit /b 1
)

python main.py

pause
