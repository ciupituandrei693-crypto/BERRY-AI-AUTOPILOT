@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title BERRY AI AUTOPILOT - Teste finale PC (local)
echo.
echo ==========================================
echo BERRY - VALIDARE WINDOWS, FARA CLOUD
echo ==========================================
echo.
if not exist ".venv\Scripts\python.exe" (
  echo [BERRY] Mediul local lipseste. Porneste intai LAUNCH_BERRY.cmd.
  pause
  exit /b 1
)
echo [BERRY] Pregatesc instrumentele gratuite de testare...
".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
if errorlevel 1 goto fail
echo [BERRY] Rulez testele automate, FFmpeg, Blender si verificarea EXE daca exista...
".venv\Scripts\python.exe" tools\pc_validation.py --full --tests
if errorlevel 1 goto fail
echo.
echo [BERRY] Testele selectate au trecut. Verifica raportul din:
echo %LOCALAPPDATA%\BERRY_AI_AUTOPILOT\reports
echo [BERRY] SKIP inseamna NEVALIDAT, nu PASS.
pause
exit /b 0
:fail
echo.
echo [BERRY] Un test a esuat sau lipsesc dependente. Verifica raportul local.
pause
exit /b 1
