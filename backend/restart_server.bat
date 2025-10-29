@echo off
REM ArbitrageVault Backend Server Restart Script
REM Phase 3 Day 7 - Products Router Fix

echo ============================================
echo ArbitrageVault Backend Server Restart
echo ============================================
echo.
echo Press Ctrl+C to stop the current server if running
echo Then press any key to start the new server...
pause

echo.
echo Starting backend server on port 8000...
echo Products Discovery endpoints will be available at:
echo   - POST /api/v1/products/discover
echo   - POST /api/v1/products/discover-with-scoring
echo   - GET  /api/v1/products/health
echo.

cd /d "%~dp0"
uvicorn app.main:app --host 0.0.0.0 --port 8000
