"""One-click Windows entrypoint for the optional PyInstaller desktop build."""
from __future__ import annotations
import os
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path


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
    configure_local_storage()
    threading.Thread(target=open_when_ready, daemon=True).start()
    import uvicorn
    print('BERRY AI AUTOPILOT | Local: http://127.0.0.1:8765')
    print('Fără publicare automată, fără GPU cloud și fără plăți.')
    uvicorn.run('berry.app:app', host='127.0.0.1', port=8765, log_level='info', reload=False)
