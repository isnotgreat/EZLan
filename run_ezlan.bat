@echo off
echo Starting EZLan with administrator privileges...

:: Check for Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Get the absolute path to main.py
set SCRIPT_PATH=%~dp0ezlan\main.py

:: Check if main.py exists
if not exist "%SCRIPT_PATH%" (
    echo Could not find main.py at: %SCRIPT_PATH%
    pause
    exit /b 1
)

:: Run with admin rights and wait for completion
powershell -Command "Start-Process python -ArgumentList '%SCRIPT_PATH%' -Verb RunAs -Wait"

:: Check if the program started successfully
if %errorlevel% neq 0 (
    echo Failed to start EZLan
    pause
    exit /b 1
)

pause