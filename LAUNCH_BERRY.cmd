@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title BERRY AI AUTOPILOT - Local Studio v1.1 RC
if exist "dist\BERRY_AI_AUTOPILOT\BERRY_AI_AUTOPILOT.exe" (
  "dist\BERRY_AI_AUTOPILOT\BERRY_AI_AUTOPILOT.exe"
  exit /b %errorlevel%
)
set "BERRY_PYTHON="
if exist ".runtime\python\python.exe" set "BERRY_PYTHON=.runtime\python\python.exe"
if not defined BERRY_PYTHON (
  where py >nul 2>nul
  if not errorlevel 1 set "BERRY_PYTHON=py -3"
)
if not defined BERRY_PYTHON (
  where python >nul 2>nul
  if not errorlevel 1 set "BERRY_PYTHON=python"
)
if not defined BERRY_PYTHON (
  echo [BERRY] Python 3.11+ nu a fost gasit.
  echo Instaleaza Python 3.11/3.12 de la python.org, apoi apasa din nou LAUNCH_BERRY.cmd.
  echo Nu a fost instalat sau descarcat nimic automat.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo [BERRY] Pregatesc mediul Python local - doar prima data...
  %BERRY_PYTHON% -m venv .venv
  if errorlevel 1 goto fail
)
if not exist ".venv\berry-ready-v11.flag" (
  echo [BERRY] Instalez dependentele gratuite - necesita internet doar prima data...
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 goto fail
  echo ready>".venv\berry-ready-v11.flag"
)
echo.
echo [BERRY] Pornesc aplicatia local la http://127.0.0.1:8765
echo [BERRY] Inchide aceasta fereastra pentru a opri aplicatia.
".venv\Scripts\python.exe" berry_launcher.py
if errorlevel 1 goto fail
exit /b 0
:fail
echo.
echo [BERRY] Pornirea a esuat. Verifica mesajele de mai sus.
pause
exit /b 1
