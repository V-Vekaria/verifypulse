@echo off
echo ================================================
echo   VerifyPulse - Starting up...
echo ================================================
echo.

cd /d %~dp0

:: Check for venv in backend (where it lives)
if not exist backend\venv\Scripts\activate.bat (
    echo No virtual environment found. Creating one...
    python -m venv backend\venv
    if errorlevel 1 (
        echo ERROR: Could not create virtual environment.
        echo Make sure Python 3.10+ is installed and on your PATH.
        pause
        exit /b 1
    )
    echo Installing dependencies...
    call backend\venv\Scripts\activate.bat
    pip install -r backend\requirements.txt
) else (
    call backend\venv\Scripts\activate.bat
)

:: Force UTF-8 so unicode characters don't crash on Windows
set PYTHONUTF8=1

:: Start backend
cd backend
echo Starting VerifyPulse API on http://localhost:8000
echo Press Ctrl+C to stop.
echo.
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
