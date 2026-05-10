@echo off
REM Setup script for Windows

echo 🚀 OpenWebUI Proxy Server Setup
echo ================================

REM Check Python version
python --version
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)
echo ✓ Python found

REM Create virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo ✓ Dependencies installed

REM Create logs directory
if not exist "logs" (
    mkdir logs
    echo ✓ Logs directory created
) else (
    echo ✓ Logs directory already exists
)

REM Copy .env.example if .env doesn't exist
if not exist ".env" (
    copy .env.example .env
    echo ✓ .env file created from .env.example
    echo ⚠️  Please edit .env with your configuration
) else (
    echo ✓ .env file already exists
)

echo.
echo Setup complete! 🎉
echo.
echo Next steps:
echo 1. Edit .env with your OpenWebUI URL
echo 2. Activate virtual environment: venv\Scripts\activate
echo 3. Run the server: python -m app.main
echo.

pause
