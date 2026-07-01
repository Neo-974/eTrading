@echo off
setlocal
title eTrading - Serveur local
cd /d "%~dp0.."

echo ============================================
echo   eTrading - Demarrage du serveur local
echo ============================================
echo.

REM --- Verifie que Python est installe ---
where python >nul 2>nul
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH.
    echo Installez Python depuis https://python.org puis relancez ce script.
    pause
    exit /b 1
)

REM --- Cree l'environnement virtuel s'il n'existe pas ---
if not exist "venv\Scripts\activate.bat" (
    echo [1/4] Creation de l'environnement virtuel...
    python -m venv venv
) else (
    echo [1/4] Environnement virtuel deja present.
)

call venv\Scripts\activate.bat

REM --- Installe les dependances (rapide si deja installees) ---
echo [2/4] Verification des dependances...
pip install -q -r requirements.txt

REM --- Cree le fichier .env s'il n'existe pas ---
if not exist ".env" (
    echo [3/4] Creation du fichier .env a partir de .env.example...
    copy .env.example .env >nul
    echo.
    echo /!\ Pensez a ouvrir le fichier .env et changer WEBHOOK_SECRET
    echo     et DASHBOARD_PASSWORD avant d'exposer le serveur a internet.
    echo.
) else (
    echo [3/4] Fichier .env deja present.
)

REM --- Le fichier .env est desormais charge automatiquement par le serveur
REM     (python-dotenv), pas besoin de le parser ici.

echo [4/4] Lancement du serveur sur http://localhost:8000 ...
echo.
echo (Laissez cette fenetre ouverte tant que vous utilisez le bot.
echo  Fermez-la ou faites Ctrl+C pour arreter le serveur.)
echo.

cd app
start "" http://localhost:8000
uvicorn main:app --host 0.0.0.0 --port 8000

pause
