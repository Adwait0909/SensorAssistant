# ========================================================
# Intelligent Electronics Project Assistant
# Windows PowerShell Automated Setup Script
# ========================================================

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Starting Intelligent Electronics Project Assistant Setup" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 1. Check Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[ERROR] Python was not found in PATH. Install Python 3.11+ from https://www.python.org" -ForegroundColor Red
    Exit 1
}

Write-Host "`n[1/5] Python Version:" -ForegroundColor Green
python --version

# 2. Virtual environment
Write-Host "`n[2/5] Setting up virtual environment (.venv)..." -ForegroundColor Green
if (-not (Test-Path -Path ".venv")) {
    python -m venv .venv
    Write-Host "Created .venv folder." -ForegroundColor Gray
} else {
    Write-Host ".venv already exists." -ForegroundColor Gray
}

# 3. Dependencies
Write-Host "`n[3/5] Activating venv and installing packages..." -ForegroundColor Green
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt

# 4. Environment config
Write-Host "`n[4/5] Checking configuration (.env)..." -ForegroundColor Green
if (-not (Test-Path -Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Copied .env.example to .env" -ForegroundColor Gray
} else {
    Write-Host ".env file already exists." -ForegroundColor Gray
}

# 5. Database init
Write-Host "`n[5/5] Initializing and seeding database..." -ForegroundColor Green
& ".\.venv\Scripts\python.exe" -m database.init_db

Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host " Setup complete! Start application by running: " -ForegroundColor Cyan
Write-Host "   .\.venv\Scripts\python.exe app.py" -ForegroundColor Yellow
Write-Host " or: " -ForegroundColor Cyan
Write-Host "   .\run_windows.bat" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan
