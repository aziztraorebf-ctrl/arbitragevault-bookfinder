@echo off
echo ========================================
echo Phase 1 Validation - ROI V1 vs V2
echo ========================================
echo.

REM Check if backend is running
echo [1/3] Checking backend availability...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Backend is not running!
    echo Please start backend first:
    echo   1. Open new terminal
    echo   2. cd backend
    echo   3. START_BACKEND.bat
    echo.
    pause
    exit /b 1
)
echo     Backend OK (http://localhost:8000)

echo.
echo [2/3] Checking Python dependencies...
python -c "import requests, pandas" >nul 2>&1
if %errorlevel% neq 0 (
    echo     Missing dependencies. Installing...
    pip install requests pandas
)
echo     Dependencies OK

echo.
echo [3/3] Running validation with 8 ASINs...
echo     This will take ~2-3 minutes...
echo.

python validate_roi_v1_vs_v2.py ^
  --base-url http://localhost:8000 ^
  --asins 0134685997,1259573545,0593655036,1982137274,B08N5WRWNW,B00FLIJJSA,B0DFMNSKAX,B07FNW9FGJ

echo.
echo ========================================
echo Validation Complete!
echo ========================================
echo.
echo Results available at:
echo   - CSV:      C:\tmp\roi_validation.csv
echo   - Summary:  C:\tmp\roi_validation_summary.md
echo.
pause
