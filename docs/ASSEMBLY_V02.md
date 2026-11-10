# BERRY AI AUTOPILOT — Assembly v0.2 (local only)

## What is implemented and tested

- Existing v0.1: 5 channels, 9 characters, 25 daily DRAFT cards, SEO templates, local KoboldCpp bridge, approvals, audit, budgets and Kill Switch.
- One Windows launch entrypoint: `LAUNCH_BERRY.cmd`; creates local `.venv` and installs minimal Python dependencies on first run, starts FastAPI bound to `127.0.0.1:8765`, opens browser after health check.
- Local Media Studio page: choose a DRAFT card, queue preview/full storyboard generation, inspect job state and download outputs.
- Local renderer: saves original character *concept art*, editable script, SRT captions and JSON manifest. If local FFmpeg is available, renders a static concept MP4. If local Piper + voice model is configured, can render a WAV and use it in the preview. No downloads or cloud inference.
- Job persistence in SQLite, bounded queue, one render worker at a time, restart interruption handling, safe file-serving by job ID.
- Server remains localhost-only; publishing, spending, OAuth and external GPU remain disabled.

## Important limitations

- Static MP4 is **not** 3D animation, AI image/video generation or finished production quality. No scene rigging, automated lipsync, original song or AI model weights are bundled.
- The user-provided ZIP archives are **source references**, not installed or audited integrations. We do not redistribute third-party sources/weights without license checks.
- `LAUNCH_BERRY.cmd` requires Python 3.11+ already installed on Windows. First-run pip installation requires Internet. Fully portable Windows EXE packaging and actual Windows launcher test remain outstanding.
- The PWA is local desktop/browser only. iPhone access requires private secure connectivity in the final phase.
- The character images are existing concept assets; check rights before redistributing the public repository or monetizing them.

## Verification

- Run `python -m pytest -q` for backend tests and local rendering tests (FFmpeg test skips if binary absent).
- Run `node --check static/app.js` to validate UI JavaScript syntax.
- For a manual smoke test: `python -m uvicorn berry.app:app --host 127.0.0.1 --port 8765`, then Media Studio.
- All media generation is local and can be stopped by closing the launcher window.

## Next local assembly phases

1. Windows launcher smoke test and portable Windows build on Windows, dependency/version locking.
2. Integrate licensed local model weights with KoboldCpp and generate reviewed scripts; no automatic factual claims.
3. VoiceStudio/Chatterbox/Piper voice workflow, faster-whisper captions, quality controls.
4. Blender fruit character rigging/visemes, ComfyUI/WanGP image/video experiments only when hardware permits.
5. ACE-Step original music integration and rights verification; do not use existing copyrighted songs without permission.
6. Render QA, preview gallery, backup, authentication hardening, then controlled distribution.
7. **Last phase only:** remote server, cloud GPU, official social API connections, publication and ads, each requiring separate explicit approval.
