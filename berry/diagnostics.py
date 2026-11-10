"""Read-only local Windows/hardware diagnostics. No downloads or AI workload."""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from . import studio


def _version(executable: str, args: list[str]) -> str:
    try:
        p = subprocess.run([executable, *args], capture_output=True, text=True, timeout=8, check=False)
        return (p.stdout or p.stderr).strip().splitlines()[0][:180] if p.returncode == 0 else 'UNVERIFIED'
    except (OSError, subprocess.TimeoutExpired, IndexError):
        return 'UNVERIFIED'


def _gpu_windows() -> list[dict]:
    if os.name != 'nt':
        return []
    ps = shutil.which('powershell.exe')
    if not ps:
        return []
    try:
        p = subprocess.run([ps, '-NoProfile', '-NonInteractive', '-Command',
             'Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM | ConvertTo-Json -Compress'],
             capture_output=True, text=True, timeout=10, check=False)
        if p.returncode:
            return []
        import json
        data = json.loads(p.stdout)
        return [{'name': str(x.get('Name', 'unknown'))[:100],
                 'reported_vram_bytes': x.get('AdapterRAM')} for x in (data if isinstance(data, list) else [data])]
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return []



def _last_validation() -> dict | None:
    folder = Path(os.environ.get('LOCALAPPDATA') or Path.home()) / 'BERRY_AI_AUTOPILOT' / 'reports'
    if not folder.is_dir():
        return None
    candidates = sorted(folder.glob('pc_validation_*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        return None
    latest = candidates[0]
    try:
        if latest.stat().st_size > 200_000:
            return None
        data = json.loads(latest.read_text(encoding='utf-8'))
        return {'timestamp_utc': data.get('timestamp_utc'),
                'counts': data.get('counts'),
                'steps': data.get('steps', [])[:12],
                'optimization_recommendations': data.get('optimization_recommendations', [])[:10],
                'blender_3d_benchmarked': data.get('blender_3d_benchmarked', False),
                'ai_model_inference_benchmarked': data.get('ai_model_inference_benchmarked', False)}
    except (OSError, ValueError, TypeError):
        return None


def report() -> dict:
    root = Path(os.environ.get('LOCALAPPDATA') or Path.home()) / 'BERRY_AI_AUTOPILOT'
    try:
        disk = shutil.disk_usage(root if root.exists() else Path.home())
        free_gib = round(disk.free / 2**30, 2)
    except OSError:
        free_gib = None
    binaries = {}
    for name, env, args in (
        ('ffmpeg', 'BERRY_FFMPEG_PATH', ['-version']),
        ('blender', 'BERRY_BLENDER_PATH', ['--version']),
        ('rhubarb', 'BERRY_RHUBARB_PATH', ['--version']),
        ('piper', 'BERRY_PIPER_PATH', ['--help']),
    ):
        path = studio.binary_path(name, env)
        binaries[name] = {'detected': bool(path), 'version': _version(path, args) if path else None}
    try:
        import fastapi, PIL, uvicorn
        imports_ok = True
    except ImportError:
        imports_ok = False
    static_ok = (studio.ROOT / 'static' / 'index.html').is_file() and (studio.ROOT / 'tools' / 'blender_fruit_scene.py').is_file()
    return {
        'local_only': True, 'cloud_used': False, 'models_benchmarked': False,
        'application': {'imports_ok': imports_ok, 'static_ok': static_ok,
                        'frozen_executable': bool(getattr(sys, 'frozen', False))},
        'system': {'os': platform.system(), 'os_release': platform.release(),
                   'cpu': platform.processor()[:100], 'python': platform.python_version(),
                   'disk_free_gib': free_gib, 'gpus': _gpu_windows()},
        'binaries': binaries, 'last_pc_validation': _last_validation(),
        'verification': 'Detectare locală, NU benchmark de inferență; pentru teste reale pornește modelele separat.',
        'next_step': 'Generează o scenă Blender 3D de 6 secunde; măsoară timpul și verifică video/voce manual.',
    }
