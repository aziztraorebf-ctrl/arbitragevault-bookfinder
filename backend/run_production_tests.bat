@echo off
echo =====================================
echo   TESTS PRODUCTION-LIKE
echo =====================================
echo.

cd /d C:\Users\azizt\Workspace\arbitragevault_bookfinder\backend

echo Verification que le serveur est lance...
echo.

curl -s http://localhost:8000/api/v1/health/ready >NUL 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Le serveur n'est pas demarre!
    echo.
    echo Veuillez d'abord executer: start_test_server.bat
    echo dans un AUTRE terminal
    echo.
    pause
    exit /b 1
)

echo [OK] Serveur detecte sur port 8000
echo.
echo Lancement des tests production-like...
echo.

python test_production_like_auto.py

pause