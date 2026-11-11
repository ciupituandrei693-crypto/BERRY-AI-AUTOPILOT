"""One-click Windows entrypoint for the optional PyInstaller desktop build."""
from __future__ import annotations
import os
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path


def load_local_configuration() -> None:
    """Read optional .env.local as plain KEY=VALUE (never execute shell code)."""
    appdir = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
    config = appdir / '.env.local'
    if not config.is_file():
        return
    allowed = {
        'BERRY_ACCESS_KEY', 'BERRY_KOBOLD_URL', 'BERRY_COMFYUI_URL', 'BERRY_COMFYUI_WORKFLOW',
        'BERRY_ACE_STEP_URL', 'BERRY_WANGP_ROOT', 'BERRY_WANGP_PYTHON', 'BERRY_WANGP_SETTINGS',
        'BERRY_WHISPER_MODEL', 'BERRY_WHISPER_PYTHON', 'BERRY_FFMPEG_PATH', 'BERRY_PIPER_PATH',
        'BERRY_PIPER_MODEL', 'BERRY_BLENDER_PATH', 'BERRY_SAPI_TTS',
        'BERRY_VOICESTUDIO_URL', 'BERRY_VOICESTUDIO_VOICE', 'BERRY_VOICESTUDIO_MODEL',
        'BERRY_RHUBARB_PATH', 'BERRY_3D_MAX_SECONDS', 'BERRY_3D_WIDTH', 'BERRY_3D_FPS',
        'BERRY_MODEL_BRIDGE_CONFIG', 'BERRY_BRIDGE_TIMEOUT',
        'BERRY_CHATTERBOX_ROOT', 'BERRY_CHATTERBOX_PYTHON',
        'BERRY_HYPERFRAMES_BIN', 'BERRY_HYPERFRAMES_GSAP_PATH', 'BERRY_OPENCLIPPER_ROOT', 'OPEN_CLIPPER_MCP_PORT',
        'BERRY_INSTAGRAM_SKILL_ROOT',
        'BERRY_GOOGLE_OAUTH_CLIENT_ID', 'BERRY_GOOGLE_OAUTH_CLIENT_SECRET_FILE',
        'BERRY_JARVIS_API_KEY', 'BERRY_SOCIAL_OAUTH_ENABLED',
        'BERRY_SOCIAL_REDIRECT_BASE', 'BERRY_YOUTUBE_REDIRECT_BASE',
        'BERRY_TIKTOK_REDIRECT_BASE', 'BERRY_INSTAGRAM_REDIRECT_BASE', 'BERRY_TIKTOK_CLIENT_KEY',
        'BERRY_TIKTOK_CLIENT_SECRET_FILE', 'BERRY_INSTAGRAM_APP_ID',
        'BERRY_INSTAGRAM_APP_SECRET_FILE',
    }
    for raw in config.read_text(encoding='utf-8-sig').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key, value = key.strip(), value.strip().strip('"')
        if key in allowed and value:
            os.environ.setdefault(key, value)


def configure_local_storage() -> Path:
    root = Path(os.environ.get('LOCALAPPDATA') or Path.home()) / 'BERRY_AI_AUTOPILOT'
    root.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault('BERRY_DB_PATH', str(root / 'berry.sqlite3'))
    os.environ.setdefault('BERRY_OUTPUT_DIR', str(root / 'outputs'))
    os.environ.setdefault('BERRY_ASSET_DIR', str(root / 'assets'))
    os.environ.setdefault('BERRY_SCRIPT_DIR', str(root / 'scripts'))
    return root


def open_when_ready():
    url = 'http://127.0.0.1:8765/'
    for _ in range(100):
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    webbrowser.open(url)
                    return
        except (OSError, urllib.error.URLError):
            time.sleep(.3)


if __name__ == '__main__':
    if '--self-test' in sys.argv:
        import json
        from berry import diagnostics
        from berry.app import app  # ensure the frozen build contains the ASGI application
        result = diagnostics.report()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result['application']['imports_ok'] and result['application']['static_ok'] else 1)
    load_local_configuration()
    configure_local_storage()
    threading.Thread(target=open_when_ready, daemon=True).start()
    import uvicorn
    print('BERRY AI AUTOPILOT | Local: http://127.0.0.1:8765')
    print('Fără publicare automată, fără GPU cloud și fără plăți.')
    uvicorn.run('berry.app:app', host='127.0.0.1', port=8765, log_level='info', reload=False)
