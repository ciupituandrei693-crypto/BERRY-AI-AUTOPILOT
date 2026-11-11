# BERRY AI AUTOPILOT — local-first Windows studio (v1.3 RC)

BERRY is a local-first FastAPI + SQLite + responsive PWA studio for five cinematic fruit-character content channels. It provides editorial planning, SEO templates, FFmpeg motion-graphics video assembly, voice/music mixing, local AI engine adapters, QA, human approvals, local scheduling, manual publishing ZIPs, offline CSV analytics, and backup.

**Run:** unzip and double-click `LAUNCH_BERRY.cmd` on Windows. Python 3.11+ is needed on first source launch; the launcher creates a virtual environment and installs the free requirements. For a Python-free destination, build the optional onedir executable on Windows with `BUILD_WINDOWS_EXE.cmd` (Windows build not yet verified). The local dashboard opens at `http://127.0.0.1:8765`.

**AI adapters** (optional, not preinstalled): ComfyUI image API, ACE-Step 1.5 music API, VoiceStudio local TTS API, WanGP Python API, faster-whisper offline subtitles, Piper/SAPI narration and KoboldCpp SEO. Each requires its own runtime and model weights. `docs/LOCAL_AI_ENGINES.md` has setup and licensing notes. Model-backed end-to-end generation has not been validated on the target hardware.

**Not included:** automatic social posting, OAuth, external servers, rented GPUs, cloud inference, paid advertising, validated model-backed cinematic 3D generation on target hardware. These are disabled and/or require further local validation. No cloud cost or posting is triggered.

**Tests:** `python -m pip install -r requirements.txt -r requirements-dev.txt && python -m pytest -q`. The v1.1 RC assembly passed 28 local tests, including mocked local AI API contracts and real FFmpeg media checks. Windows exe and AI models need on-device testing.

Read [Romanian README](README_RO.md), [local engine guide](docs/LOCAL_AI_ENGINES.md), [status matrix](docs/STATUS_LOCAL_V11.md) and [security](SECURITY.md).

## Local completion through PC validation (v1.3 RC)

A user-configured offline bridge now supports LivePortrait, MuseTalk, LatentSync and Hunyuan3D local Python entrypoints. This is **not** a claim that weights are installed or the models have been executed successfully. The source ZIP archives supplied in chat could not be inspected byte-for-byte in the current runtime. CLI templates must be checked against the exact source versions. See `tools/model_bridge.example.json` and `docs/LOCAL_FINAL_STAGES_1_TO_11.md`.

For the Windows-only real performance and app checks, run `TESTE_FINALE_PC.cmd`. This creates a local JSON report, with PASS/FAIL/SKIP for FastAPI/SQLite, FFmpeg, Blender, Windows EXE (if built), and pytest. It does not automatically run heavyweight generative models or enable external services. To build the Windows EXE, run `BUILD_WINDOWS_EXE.cmd` first. **Actual Windows hardware results remain unverified until run on the user's PC.**

## Guided Windows installation of local engines

Double-click `INSTALARE_TOATE_COMPONENTELE.cmd` to interactively install free local prerequisites, Blender, Rhubarb Windows executable, ComfyUI portable, VoiceStudio, Piper, faster-whisper and PyInstaller, plus optional model downloads and isolated AI runtimes. It prompts for downloads and does not enable cloud services or social posting. Heavy model installation depends on GPU, disk space, licenses and upstream Windows support. The script has **not been executed on the user's Windows machine**. See `docs/INSTALARE_COMPLETA_WINDOWS.md`; send the generated `install_*.json` and `pc_validation_*.json` reports for diagnosis.

## Google OAuth / YouTube (PREGĂTIRE OFFLINE)

În pagina **Integrări**, BERRY afișează cinci sloturi YouTube și permite salvarea unui plan local cu nume/ID canal, fără verificarea identității. `youtube.readonly` este singurul scope pregătit; conectarea Google, callbackul și uploadul răspund cu HTTP 423 și nu stochează tokenuri. Butonul Google este dezactivat. Vezi [ghidul de pregătire](docs/YOUTUBE_GOOGLE_OAUTH_PREPARATION.md).
