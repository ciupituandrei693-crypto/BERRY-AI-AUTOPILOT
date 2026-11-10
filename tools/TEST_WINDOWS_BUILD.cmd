@echo off
setlocal EnableExtensions
cd /d "%~dp0\.."
set "EXE=dist\BERRY_AI_AUTOPILOT\BERRY_AI_AUTOPILOT.exe"
if not exist "%EXE%" (
 echo [BERRY] EXE nu exista. Ruleaza BUILD_WINDOWS_EXE.cmd.
 exit /b 1
)
echo [BERRY] Smoke test executabil Windows...
"%EXE%" --self-test > "dist\berry-windows-self-test.json"
if errorlevel 1 (
 echo [BERRY] Test Windows esuat. Vezi dist\berry-windows-self-test.json
 exit /b 1
)
echo [BERRY] Self-test executabil a trecut. Testul GPU/Blender trebuie rulat separat.
exit /b 0
