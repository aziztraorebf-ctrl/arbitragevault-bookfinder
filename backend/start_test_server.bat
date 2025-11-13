@echo off
echo =====================================
echo   DEMARRAGE SERVEUR TEST LOCAL
echo =====================================
echo.

cd /d C:\Users\azizt\Workspace\arbitragevault_bookfinder\backend

echo [1/3] Installation des dependances...
pip install fastapi uvicorn httpx python-dotenv keepa sqlalchemy asyncpg python-multipart 2>NUL

echo.
echo [2/3] Demarrage du serveur FastAPI...
echo.
echo Le serveur va demarrer sur http://localhost:8000
echo.
echo IMPORTANT: Laissez cette fenetre ouverte!
echo           Ouvrez un NOUVEAU terminal pour les tests
echo.
echo =====================================
echo.

uvicorn app.main:app --reload --port 8000 --log-level info