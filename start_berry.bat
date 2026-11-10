@echo off
setlocal
cd /d "%~dp0"
title BERRY AI AUTOPILOT LOCAL
where py >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON=py -3"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Python 3.11+ nu a fost gasit. Instaleaza Python 3.12 de la python.org.
    pause
    exit /b 1
  )
  set "PYTHON=python"
)
if not exist ".venv\Scripts\python.exe" (
  echo [BERRY] Creez mediul local...
  %PYTHON% -m venv .venv
  if errorlevel 1 goto error
)
if not exist ".venv\ready.flag" (
  echo [BERRY] Instalez dependentele locale gratuite...
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 goto error
  echo ready>".venv\ready.flag"
)
echo [BERRY] Deschid http://127.0.0.1:8765
start "" "http://127.0.0.1:8765"
".venv\Scripts\python.exe" -m uvicorn berry.app:app --host 127.0.0.1 --port 8765
pause
exit /b 0
:error
echo Instalarea nu a reusit. Verifica Python si conexiunea internet necesara doar pentru pachetele pip.
pause
exit /b 1
