@echo off
REM ============================================
REM AppleTrader Pro - Application Launcher
REM ============================================

echo.
echo ========================================
echo  AppleTrader Pro
echo  Institutional Trading Dashboard
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.9+ from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [1/3] Checking dependencies...
echo.

REM Check if PyQt6 is installed
python -c "import PyQt6" >nul 2>&1
if %errorlevel% neq 0 (
    echo PyQt6 not found. Installing dependencies...
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies!
        pause
        exit /b 1
    )
) else (
    echo ✓ All dependencies installed
)

echo.
echo [2/3] Starting AppleTrader Pro...
echo.

REM Launch the application
python main.py

echo.
echo [3/3] Application closed.
echo.

pause
