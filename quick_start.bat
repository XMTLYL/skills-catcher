@echo off
REM Quick Start Script for GitHub Skill Indexer (Windows)
REM This script helps you quickly set up and run the project

echo ============================================================
echo GitHub Skill Indexer - Quick Start
echo ============================================================
echo.

REM Check Python version
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version: %PYTHON_VERSION%
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created
) else (
    echo Virtual environment already exists
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Virtual environment activated
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet
echo Dependencies installed
echo.

REM Check if .env exists
if not exist ".env" (
    echo .env file not found
    echo Creating .env from template...
    copy .env.example .env
    echo.
    echo ============================================================
    echo IMPORTANT: Please edit .env file and fill in:
    echo    - GITHUB_TOKEN (required)
    echo    - DATABASE_URL (required)
    echo ============================================================
    echo.
    pause
) else (
    echo .env file exists
)
echo.

REM Check database connection
echo Checking database connection...
python -c "from src.database import engine; engine.connect()" >nul 2>&1
if errorlevel 1 (
    echo Database connection failed
    echo.
    echo Please check your DATABASE_URL in .env file
    echo Example: mysql+pymysql://user:password@localhost:3306/skill_index?charset=utf8mb4
    exit /b 1
)
echo Database connection successful
echo.

REM Initialize database
echo Initializing database...
python scripts\init_db.py
if errorlevel 1 (
    echo Database initialization failed
    exit /b 1
)
echo Database initialized
echo.

REM Create logs directory
if not exist "logs" (
    mkdir logs
    echo Logs directory created
)

echo ============================================================
echo Setup completed successfully!
echo ============================================================
echo.
echo Next steps:
echo.
echo 1. Run Code Search:
echo    python main.py code_search
echo.
echo 2. Scan a specific repository:
echo    python main.py repo_scan --repo anthropics/anthropic-quickstarts
echo.
echo 3. View statistics:
echo    python main.py stats
echo.
echo 4. Get help:
echo    python main.py --help
echo.
echo For detailed documentation, see:
echo   - README.md
echo   - docs\deployment.md
echo   - docs\PROJECT_SUMMARY.md
echo.
echo ============================================================
pause
