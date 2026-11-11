"""Offline Instagram content checks from the user's verified MIT-licensed ZIP.

Only three reviewed, SHA256-pinned Python scripts are invoked on explicit
request. No Instagram API, account login, publishing or cloud connections.
The heuristics are written primarily for English and are advisory for Romanian.
"""
from __future__ import annotations
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = {
    'hook': ('skills/ig-reel/hookscore.py',
             '8e1d10edda81dcdf0f18cd24ae37716a7ca30873af777e0f65383089addfe69e'),
    'beats': ('skills/ig-reel/beats.py',
              '2f8a4ecb9e28be0a09a35c418d45665cf1d5aa16e7f852ed051e62f1c6983414'),
    'caption': ('skills/ig-caption/caption.py',
                '7952b512abaac7521d6f5838ef7a2c6b04c06146372fd658466814a7e9893917'),
}
LIMITS = {'hook': 240, 'beats': 5000, 'caption': 2200}


class InstagramToolError(ValueError):
    pass


def source_root() -> Path:
    return Path(os.getenv('BERRY_INSTAGRAM_SKILL_ROOT',
                          str(ROOT / 'local_engines' / 'InstagramAgentSkill')))


def checked_script(kind: str) -> Path:
    if kind not in SCRIPTS:
        raise InstagramToolError('Tip de analiza necunoscut')
    root = source_root().resolve()
    path = (root / SCRIPTS[kind][0]).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise InstagramToolError('Importa mai intai arhiva Instagram Agent Skill verificata')
    if hashlib.sha256(path.read_bytes()).hexdigest() != SCRIPTS[kind][1]:
        raise InstagramToolError('Fisierul sursa a fost modificat; executia este blocata')
    return path


def analyze(kind: str, text: str, *, target: float = 15.0, keywords: str = '') -> dict:
    if kind not in SCRIPTS:
        raise InstagramToolError('Tip de analiza necunoscut')
    if not text or not text.strip() or len(text) > LIMITS[kind] or '\x00' in text:
        raise InstagramToolError(f'Textul trebuie sa aiba 1-{LIMITS[kind]} caractere')
    if not 5 <= target <= 600:
        raise InstagramToolError('Durata trebuie sa fie intre 5 si 600 secunde')
    if len(keywords) > 200:
        raise InstagramToolError('Prea multe cuvinte cheie')
    script = checked_script(kind)
    args = [sys.executable, '-I', str(script), '--json']
    if kind == 'beats':
        args.extend(['--target', str(target)])
    if kind == 'caption' and keywords:
        args.extend(['--keywords', keywords])
    env = {k: os.environ[k] for k in ('PATH', 'SYSTEMROOT', 'WINDIR') if k in os.environ}
    env.update({'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8', 'PYTHONNOUSERSITE': '1'})
    try:
        run = subprocess.run(args, input=text, text=True, encoding='utf-8',
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             cwd=str(script.parent), env=env, timeout=8, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise InstagramToolError('Instrumentul local nu a putut rula') from exc
    if run.returncode != 0 or len(run.stdout) > 100_000:
        raise InstagramToolError('Analiza locala a esuat sau a depasit limita')
    try:
        result = json.loads(run.stdout)
    except json.JSONDecodeError as exc:
        raise InstagramToolError('Rezultat JSON invalid') from exc
    return {
        'kind': kind, 'engine': 'instagram-agent-skill-user-zip',
        'offline': True, 'published': False, 'account_connected': False,
        'review_required': True, 'language_note': (
            'Scorurile si recomandarile sursei sunt optimizate pentru engleza; '
            'in romana sunt orientative, nu statistici reale de performanta.'),
        'result': result,
    }
