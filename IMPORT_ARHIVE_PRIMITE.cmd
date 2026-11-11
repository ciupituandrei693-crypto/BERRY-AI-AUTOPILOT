@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title BERRY - Importul celor trei arhive deja trimise
echo ================================================
echo BERRY - IMPORT ZIP LOCAL, FARA CLOUD SAU PUBLICARE
echo ================================================
echo Pune in folderul incoming urmatoarele arhive originale:
echo   instagram-agent-skill-main(2).zip
echo   hyperframes-main(2).zip
echo   OpenClipper-master.zip
echo.
if not exist "incoming" mkdir "incoming"
set "BERRY_PYTHON="
if exist ".venv\Scripts\python.exe" set BERRY_PYTHON="%CD%\.venv\Scripts\python.exe"
if not defined BERRY_PYTHON (
 where py >nul 2>nul
 if not errorlevel 1 (
  py -3.11 --version >nul 2>nul
  if not errorlevel 1 set "BERRY_PYTHON=py -3.11"
 )
)
if not defined BERRY_PYTHON (
 where python >nul 2>nul
 if not errorlevel 1 set "BERRY_PYTHON=python"
)
if not defined BERRY_PYTHON (
 echo [EROARE] Python nu a fost gasit. Ruleaza mai intai INSTALARE_TOATE_COMPONENTELE.cmd
 pause
 exit /b 1
)
echo Verific integritatea arhivelor si SHA256...
%BERRY_PYTHON% "tools\import_user_archives.py" --zip-dir "%CD%\incoming" --project-root "%CD%"
if errorlevel 1 (
 echo [EROARE] Lipsesc arhive sau continutul difera de versiunea verificata.
 pause
 exit /b 1
)
echo.
choice /C DN /N /M "Importa local sursele verificate? [D=Da / N=Nu] "
if errorlevel 2 exit /b 0
%BERRY_PYTHON% "tools\import_user_archives.py" --zip-dir "%CD%\incoming" --project-root "%CD%" --extract
if errorlevel 1 (
 echo [EROARE] Import incomplet. Nu se suprascriu foldere existente.
) else (
 echo [BERRY] Sursele au fost importate local. Motoarele nu sunt instalate automat.
)
pause
