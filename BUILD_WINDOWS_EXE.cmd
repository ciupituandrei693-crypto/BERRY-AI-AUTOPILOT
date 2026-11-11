@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title BERRY - Windows standalone build
where py >nul 2>nul
if not errorlevel 1 (set "PY=py -3") else (set "PY=python")
%PY% --version >nul 2>nul
if errorlevel 1 (
 echo [BERRY] Pentru COMPILARE este necesar Python 3.11+ pe Windows.
 echo [BERRY] Dupa compilare, executabilul nu necesita Python pe PC-ul destinatie.
 pause
 exit /b 1
)
if not exist ".build-venv\Scripts\python.exe" (
 %PY% -m venv .build-venv
 if errorlevel 1 goto fail
)
".build-venv\Scripts\python.exe" -m pip install -r requirements.txt "pyinstaller>=6,<7"
if errorlevel 1 goto fail
".build-venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onedir --console --name BERRY_AI_AUTOPILOT --add-data "static;static" --add-data "tools\wangp_worker.py;tools" --add-data "tools\whisper_worker.py;tools" --add-data "tools\blender_fruit_scene.py;tools" --hidden-import berry.app --hidden-import berry.jarvis_api --hidden-import berry.hyperframes_bridge --hidden-import berry.social_oauth --hidden-import berry.social_routes --hidden-import cryptography --hidden-import berry.model_bridge --hidden-import berry.three_d --hidden-import berry.diagnostics --collect-all imageio_ffmpeg --hidden-import uvicorn.logging --hidden-import uvicorn.loops.auto --hidden-import uvicorn.loops.asyncio --hidden-import uvicorn.protocols.http.auto --hidden-import uvicorn.protocols.http.h11_impl --hidden-import uvicorn.lifespan.on --hidden-import multipart --hidden-import PIL.WebPImagePlugin berry_launcher.py
if errorlevel 1 goto fail
echo.
echo [BERRY] BUILD finalizat: dist\BERRY_AI_AUTOPILOT\BERRY_AI_AUTOPILOT.exe
call tools\TEST_WINDOWS_BUILD.cmd
if errorlevel 1 goto fail
echo [BERRY] PASTREAZA tot folderul dist\BERRY_AI_AUTOPILOT, nu doar exe-ul.
pause
exit /b 0
:fail
echo [BERRY] Compilarea a esuat. Verifica logul.
pause
exit /b 1
