@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Asteriax Verse

if exist ".venv\Scripts\pythonw.exe" goto launch

echo.
echo ============================================================
echo   ASTERIAX VERSE - PREMIERE INSTALLATION
echo ============================================================
echo.
echo Creation de l'environnement Python...

where py.exe >nul 2>&1
if not errorlevel 1 goto use_py

where python.exe >nul 2>&1
if errorlevel 1 goto no_python
python.exe -m venv ".venv"
if errorlevel 1 goto install_error
goto install_components

:use_py
py.exe -3 -m venv ".venv"
if errorlevel 1 goto install_error

:install_components
echo Installation des composants graphiques...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check --upgrade pip
if errorlevel 1 goto install_error
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r "requirements.txt"
if errorlevel 1 goto install_error

:launch
if not exist ".venv\Scripts\pythonw.exe" goto install_error
start "" ".venv\Scripts\pythonw.exe" "%~dp0main.py"
exit /b 0

:no_python
echo.
echo Python 3 n'est pas installe ou n'est pas detecte.
echo Installez-le depuis : https://www.python.org/downloads/windows/
echo Cochez "Add Python to PATH", puis relancez LANCER.bat.
echo.
pause
exit /b 1

:install_error
echo.
echo L'installation a echoue.
echo Verifiez votre connexion Internet puis relancez LANCER.bat.
echo.
pause
exit /b 1

