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

REM --- Cherche une version Python compatible (3.11/3.12/3.13) via le
REM     lanceur "py", pour eviter les versions trop recentes (ex: 3.14)
REM     qui n'ont pas encore de paquets precompiles pour certaines librairies.
set "PYCMD="
py -3.12 --version >nul 2>nul && set "PYCMD=py -3.12"
if not defined PYCMD (py -3.13 --version >nul 2>nul && set "PYCMD=py -3.13")
if not defined PYCMD (py -3.11 --version >nul 2>nul && set "PYCMD=py -3.11")
if not defined PYCMD (
    echo [ATTENTION] Aucune version Python 3.11/3.12/3.13 detectee.
    echo Ce projet est plus fiable avec l'une de ces versions ^(les
    echo versions tres recentes de Python, comme 3.14, manquent parfois
    echo de paquets precompiles pour certaines dependances^).
    echo.
    echo Si l'installation qui suit echoue, installez Python 3.12 depuis
    echo https://python.org ^(cochez "Add python.exe to PATH"^), supprimez
    echo le dossier "venv" de ce projet, puis relancez ce script.
    echo.
    set "PYCMD=python"
)
echo Python utilise: %PYCMD%

REM --- Cree l'environnement virtuel s'il n'existe pas ---
if not exist "venv\Scripts\activate.bat" (
    echo [1/4] Creation de l'environnement virtuel...
    %PYCMD% -m venv venv
) else (
    echo [1/4] Environnement virtuel deja present.
)

call venv\Scripts\activate.bat

REM --- Installe les dependances (rapide si deja installees) ---
echo [2/4] Verification des dependances...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERREUR] L'installation des dependances a echoue.
    echo Cela arrive parfois si votre version de Python est tres recente.
    echo Essayez de mettre pip a jour puis relancez :
    echo     venv\Scripts\python -m pip install --upgrade pip
    echo Si le probleme persiste, installez Python 3.11 ou 3.12 depuis
    echo https://python.org et relancez ce script.
    pause
    exit /b 1
)

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
