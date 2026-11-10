@echo off
setlocal
cd /d "%~dp0"
call "%~dp0INSTALARE_COMPONENTE_LOCALE.cmd"
exit /b %errorlevel%
