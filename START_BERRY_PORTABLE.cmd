@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title BERRY AI AUTOPILOT - Windows Portable
if not exist "%~dp0BERRY_AI_AUTOPILOT.exe" (
  echo [BERRY] Executabilul lipseste. Extrage INTREGUL folder ZIP, nu doar launcherul.
  pause
  exit /b 1
)
echo [BERRY] Pornire locala: http://127.0.0.1:8765
echo [BERRY] Fara server extern, GPU cloud, plata sau publicare automata.
"%~dp0BERRY_AI_AUTOPILOT.exe"
if errorlevel 1 (
  echo [BERRY] Pornirea a esuat. Pastreaza folderul complet si verifica antivirusul/logul.
  pause
  exit /b 1
)
exit /b 0
