@echo off
REM ========================================================
REM Intelligent Electronics Project Assistant
REM Windows Automated Setup Script (PowerShell / CMD)
REM ========================================================

echo ========================================================
echo  Starting Intelligent Electronics Project Assistant Setup
echo ========================================================

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your system PATH.
    echo Please install Python 3.11 or later from python.org
    pause
    exit /b 1
)

echo.
echo [1/5] Checking Python version...
python --version

echo.
echo [2/5] Creating Python virtual environment (.venv)...
if not exist .venv (
    python -m venv .venv
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)

echo.
echo [3/5] Activating virtual environment and installing requirements...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [4/5] Checking environment configuration...
if not exist .env (
    echo Copying .env.example to .env...
    copy .env.example .env
) else (
    echo .env file already present.
)

echo.
echo [5/5] Initializing and seeding database...
python -m database.init_db

echo.
echo ========================================================
echo  Setup Completed Successfully!
echo  Run "run_windows.bat" or "python app.py" to start.
echo ========================================================
pause
