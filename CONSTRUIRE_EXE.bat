@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Construction Asteriax Verse EXE

if not exist ".venv\Scripts\python.exe" goto no_environment

echo.
echo ============================================================
echo   ASTERIAX VERSE - CONSTRUCTION DE L'EXE WINDOWS
echo ============================================================
echo.

".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r "requirements-build.txt"
if errorlevel 1 goto build_error

".venv\Scripts\pyinstaller.exe" --noconfirm --clean "AsteriaxVerse.spec"
if errorlevel 1 goto build_error

echo.
echo Termine : dist\AsteriaxVerse.exe
echo.
explorer.exe "%~dp0dist"
pause
exit /b 0

:no_environment
echo.
echo Lancez d'abord LANCER.bat une fois pour preparer Python.
echo.
pause
exit /b 1

:build_error
echo.
echo La construction a echoue. Consultez les messages ci-dessus.
echo.
pause
exit /b 1

