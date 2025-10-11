@echo off
echo ========================================
echo Starting ArbitrageVault Backend (Local)
echo ========================================
echo.

REM Check if virtual environment exists
if exist venv\ (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Warning: No virtual environment found at venv\
    echo Using system Python...
)

echo.
echo Starting Uvicorn server...
echo Backend will be available at: http://localhost:8000
echo Press CTRL+C to stop
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
