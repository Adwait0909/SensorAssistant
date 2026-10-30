@echo off
REM ========================================================
REM Intelligent Electronics Project Assistant
REM Windows Runner Script
REM ========================================================

echo ========================================================
echo  Launching Intelligent Electronics Project Assistant
echo ========================================================

if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

echo Starting Flask server on http://127.0.0.1:5000 ...
python app.py
pause
