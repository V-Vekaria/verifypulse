@echo off
echo ================================================
echo   VerifyPulse - Starting up...
echo ================================================
echo.

cd /d %~dp0

:: Activate virtual environment
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo ERROR: No virtual environment found.
    echo Run: python -m venv venv
    pause
    exit /b 1
)

:: Start backend
cd backend
echo Starting VerifyPulse API on http://localhost:8000
echo Press Ctrl+C to stop.
echo.
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 5000
