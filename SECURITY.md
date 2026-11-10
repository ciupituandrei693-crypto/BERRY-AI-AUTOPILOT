# Security — BERRY v1.1 RC

BERRY is a **local-only** studio. Its default launcher binds `127.0.0.1:8765`. It has no social publishing, cloud GPU, server provisioning, payment execution, or OAuth integration. The kill switch is active by default. Do not expose port 8765 to LAN/Internet; the optional `BERRY_ACCESS_KEY` is only an additional local protection, not a replacement for TLS/network access control.

Engine URLs are restricted to HTTP loopback with an explicit port. Redirects are refused and downloads have byte limits. Local AI engines run only after explicit user actions and require separate model/runtime setup. No model downloads or auto-installations are triggered by BERRY AI job submission.

Imported media is size-limited; images are decoded and converted with Pillow; MP4 is signature-checked and first-frame validated by FFmpeg. Do not assume content is licensed: QA requires manual rights, factual and disclosure checks. Generated audio and AI images also need license checks.

`.env.local`, `.env`, data, database, outputs, media, model weights, logs and secrets are excluded from Git. Do not publish them. A public repository may contain project source and artwork, but rights to redistribute images and third-party libraries should be checked separately.

**Known limitations:** user-facing local server is not a hardened remote service; optional subprocess AI engines and their own code/models are outside BERRY's sandbox; large video/audio rendering can exhaust CPU/RAM/disk. Never run untrusted workflows or model weights. WanGP has its own Community License; VoiceStudio is AGPL-3.0; Hunyuan3D has special Community License conditions. Review licensing before commercial use/distribution.
