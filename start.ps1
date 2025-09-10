# ArbitrageVault - Script de démarrage local
Write-Host "🚀 Démarrage ArbitrageVault en mode développement..." -ForegroundColor Cyan

# Vérifier si les dépendances sont installées
if (!(Test-Path "frontend/node_modules")) {
    Write-Host "📦 Installation des dépendances frontend..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    Set-Location ..
}

if (!(Test-Path "backend/.venv")) {
    Write-Host "🐍 Création de l'environnement Python virtuel..." -ForegroundColor Yellow
    Set-Location backend
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    Set-Location ..
}

Write-Host "✅ Démarrage des services..." -ForegroundColor Green
Write-Host ""
Write-Host "Frontend disponible sur: http://localhost:5173" -ForegroundColor Blue
Write-Host "Backend disponible sur: http://localhost:8000" -ForegroundColor Blue
Write-Host ""
Write-Host "Appuyez sur Ctrl+C pour arrêter les services" -ForegroundColor Yellow

# Démarrer le backend en arrière-plan
Start-Process -FilePath "powershell" -ArgumentList "-Command", "cd backend; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

# Attendre 2 secondes puis démarrer le frontend
Start-Sleep -Seconds 2
Set-Location frontend
npm run dev