@echo off
setlocal
cd /d "%~dp0"
title BERRY - Instalare TOATE componentele locale
echo ================================================
echo BERRY - INSTALARE ASISTATA, DOAR PE WINDOWS
echo ================================================
echo Instaleaza gratuit Blender, Rhubarb, ComfyUI, VoiceStudio,
echo Piper, faster-whisper, PyInstaller si pregateste motoarele AI.
echo Modelele mari si mediile CUDA cer confirmare si spatiu liber.
echo Nu activeaza server extern, GPU cloud, OAuth sau plati.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0INSTALARE_COMPONENTE_LOCALE.ps1"
if errorlevel 1 (
 echo [BERRY] Instalarea a intampinat o eroare.
) else (
 echo [BERRY] Procedura s-a incheiat. Verifica raportul install_*.json.
 echo [BERRY] Ruleaza TESTE_FINALE_PC.cmd pentru validare.
)
pause
