@echo off
setlocal
cd /d "%~dp0"
title BERRY - Instalare componente locale
echo Instaleaza doar componente gratuite, cu confirmare la fiecare pas.
echo Poate necesita internet pentru descarcari gratuite.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0INSTALARE_COMPONENTE_LOCALE.ps1"
if errorlevel 1 (
 echo Instalarea a intampinat o eroare. Verifica mesajele de mai sus.
) else (
 echo Procedura s-a incheiat. Ruleaza TESTE_FINALE_PC.cmd.
)
pause
