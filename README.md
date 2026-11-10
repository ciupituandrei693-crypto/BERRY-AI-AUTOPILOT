# BERRY AI AUTOPILOT — local-first Windows studio (v1.1 RC)

BERRY is a local-first FastAPI + SQLite + responsive PWA studio for five cinematic fruit-character content channels. It provides editorial planning, SEO templates, FFmpeg motion-graphics video assembly, voice/music mixing, local AI engine adapters, QA, human approvals, local scheduling, manual publishing ZIPs, offline CSV analytics, and backup.

**Run:** unzip and double-click `LAUNCH_BERRY.cmd` on Windows. Python 3.11+ is needed on first source launch; the launcher creates a virtual environment and installs the free requirements. For a Python-free destination, build the optional onedir executable on Windows with `BUILD_WINDOWS_EXE.cmd` (Windows build not yet verified). The local dashboard opens at `http://127.0.0.1:8765`.

**AI adapters** (optional, not preinstalled): ComfyUI image API, ACE-Step 1.5 music API, VoiceStudio local TTS API, WanGP Python API, faster-whisper offline subtitles, Piper/SAPI narration and KoboldCpp SEO. Each requires its own runtime and model weights. `docs/LOCAL_AI_ENGINES.md` has setup and licensing notes. Model-backed end-to-end generation has not been validated on the target hardware.

**Not included:** automatic social posting, OAuth, external servers, rented GPUs, cloud inference, paid advertising, validated cinematic 3D character animation/rigging/lip-sync. These are disabled and/or require further local validation. No cloud cost or posting is triggered.

**Tests:** `python -m pip install -r requirements.txt -r requirements-dev.txt && python -m pytest -q`. The v1.1 RC assembly passed 28 local tests, including mocked local AI API contracts and real FFmpeg media checks. Windows exe and AI models need on-device testing.

Read [Romanian README](README_RO.md), [local engine guide](docs/LOCAL_AI_ENGINES.md), [status matrix](docs/STATUS_LOCAL_V11.md) and [security](SECURITY.md).
