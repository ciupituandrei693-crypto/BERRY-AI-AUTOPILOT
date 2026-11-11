"""HyperFrames local CLI bridge: BERRY-authored HTML -> reviewable MP4.

No arbitrary HTML upload, remote media, shell, cloud render or publish commands.
The source artwork is bundled/local. Rendering is opt-in, one job at a time.
"""
from __future__ import annotations

import base64
import html
import json
import os
import shutil
import subprocess
import threading
from pathlib import Path

from . import db, studio

ROOT = Path(__file__).resolve().parents[1]
LOCK = threading.Semaphore(1)
DURATIONS = {'short15': 15, 'main90': 90, 'longform': 300}
CHANNEL_ART = studio.CHARACTER_ART


def cli() -> str | None:
    candidate = os.getenv('BERRY_HYPERFRAMES_BIN', '').strip()
    if not candidate:
        return None
    p = Path(candidate).expanduser()
    return str(p.resolve()) if p.is_file() and p.suffix.lower() in ('.cmd', '.exe', '.js', '.mjs') else None


def init() -> None:
    with db.connection() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS hyperframes_jobs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL REFERENCES items(id),
            status TEXT NOT NULL DEFAULT 'QUEUED',
            duration_seconds INTEGER NOT NULL,
            error TEXT,
            output_path TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL)''')
        con.execute("UPDATE hyperframes_jobs SET status='INTERRUPTED',updated_at=? WHERE status IN ('QUEUED','RUNNING')",
                    (db.utcnow(),))


def status() -> dict:
    executable = cli()
    return {'source': 'USER_UPLOADED_HYPERFRAMES_ZIP',
            'cli_configured': bool(executable),
            'ready_for_local_render': bool(executable),
            'render_tested_here': False,
            'external_publishing_enabled': False,
            'requires': ['Node.js 22+', 'HyperFrames CLI', 'FFmpeg', 'Chromium local'],
            'note': 'Render manual doar din HTML generat de BERRY; concept motion graphics, NU video AI 3D'}


def _job(job_id: int) -> dict | None:
    j = db.one_row('SELECT id,item_id,status,duration_seconds,error,created_at,updated_at FROM hyperframes_jobs WHERE id=?',
                   (job_id,))
    if j:
        j['video_ready'] = j['status'] == 'DONE'
        j['published'] = False
    return j


def jobs() -> list[dict]:
    return [_job(x['id']) for x in db.all_rows('SELECT id FROM hyperframes_jobs ORDER BY id DESC LIMIT 50')]


def start(item_id: int) -> dict:
    executable = cli()
    if not executable:
        raise ValueError('Configureaza BERRY_HYPERFRAMES_BIN cu CLI-ul local instalat')
    item = db.one_row('SELECT * FROM items WHERE id=?', (item_id,))
    if not item:
        raise LookupError('Materialul nu exista')
    if item['content_type'] == 'image':
        raise ValueError('HyperFrames este pentru video; pentru imagini foloseste Media Studio')
    if item['status'] != 'DRAFT':
        raise ValueError('Materialul trebuie sa fie DRAFT')
    duration = DURATIONS[item['content_type']]
    with db.connection() as con:
        if con.execute("SELECT 1 FROM hyperframes_jobs WHERE status IN ('QUEUED','RUNNING') LIMIT 1").fetchone():
            raise ValueError('Exista deja o randare HyperFrames activa')
        now = db.utcnow()
        cur = con.execute('''INSERT INTO hyperframes_jobs(item_id,duration_seconds,created_at,updated_at)
                             VALUES(?,?,?,?)''', (item_id, duration, now, now))
        job_id = cur.lastrowid
        db.audit(con, 'hyperframes_local_queued', {'job_id': job_id, 'item_id': item_id})
    threading.Thread(target=_worker, args=(job_id, executable), daemon=True,
                     name=f'berry-hyperframes-{job_id}').start()
    return _job(job_id)


def _html(item: dict, duration: int, art: Path) -> str:
    """Offline composition, no scripts, no network dependencies, no user HTML."""
    if art.stat().st_size > 10_000_000:
        raise ValueError('Imaginea depaseste 10 MB')
    ext = art.suffix.lower()
    mime = {'.webp': 'image/webp', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg'}.get(ext)
    if not mime:
        raise ValueError('Format imagine nesuportat')
    encoded = base64.b64encode(art.read_bytes()).decode('ascii')
    title = html.escape(item['title'][:100], quote=True)
    topic = html.escape(item['topic'][:180], quote=True)
    channel = html.escape(item['channel_id'].upper(), quote=True)
    # A deliberately static, seekable composition: it renders a branded concept,
    # not an AI animated character. No external CSS/fonts/JS/media.
    return f'''<!doctype html>
<html lang="ro"><head><meta charset="UTF-8">
<meta name="viewport" content="width=360, height=640">
<title>BERRY LOCAL</title>
<style>
*{{box-sizing:border-box}}html,body{{margin:0;width:360px;height:640px;overflow:hidden;
background:#0b0b1c;color:white;font-family:Arial,Helvetica,sans-serif}}
#root{{width:360px;height:640px;position:relative;overflow:hidden}}
.bg{{position:absolute;inset:0;background:linear-gradient(150deg,#141a40,#311449 60%,#0b0b1c)}}
.glow{{position:absolute;left:15px;top:72px;width:330px;height:390px;border-radius:50%;
background:radial-gradient(ellipse,#7947cc77,transparent 70%)}}
img{{position:absolute;left:15px;top:90px;width:330px;height:345px;object-fit:contain}}
.top{{position:absolute;left:18px;top:24px;letter-spacing:3px;font-size:13px;font-weight:800;color:#e1c5ff}}
.title{{position:absolute;left:20px;right:20px;bottom:112px;font-size:25px;font-weight:800;
text-align:center;line-height:1.16;text-shadow:0 2px 8px #000}}
.topic{{position:absolute;left:24px;right:24px;bottom:55px;font-size:13px;line-height:1.35;
text-align:center;color:#dfd8ee}}
.footer{{position:absolute;left:0;right:0;bottom:15px;text-align:center;font-size:10px;letter-spacing:2px;color:#a6a0ba}}
</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{duration}" data-width="360" data-height="640">
<div class="bg"></div><div class="glow"></div>
<div class="top">BERRY AI · {channel}</div>
<img alt="" src="data:{mime};base64,{encoded}">
<div class="title">{title}</div><div class="topic">{topic}</div>
<div class="footer">LOCAL CONCEPT · REVIEW REQUIRED</div></div>
</body></html>'''


def _set(job_id: int, status: str, error: str | None = None, output: str | None = None) -> None:
    with db.connection() as con:
        con.execute('UPDATE hyperframes_jobs SET status=?,error=?,output_path=?,updated_at=? WHERE id=?',
                    (status, error, output, db.utcnow(), job_id))
        db.audit(con, 'hyperframes_local_status', {'job_id': job_id, 'status': status})


def _worker(job_id: int, executable: str) -> None:
    with LOCK:
        try:
            _set(job_id, 'RUNNING')
            job = _job(job_id)
            item = db.one_row('SELECT * FROM items WHERE id=?', (job['item_id'],))
            if not item:
                raise ValueError('Materialul nu mai exista')
            output_root = Path(os.getenv('BERRY_OUTPUT_DIR', str(studio.OUTPUT_ROOT))).resolve()
            work = output_root / f'hyperframes_{job_id:06d}'
            work.mkdir(parents=True, exist_ok=True)
            assets = Path(os.getenv('BERRY_ASSET_DIR', str(ROOT / 'data' / 'assets')))
            uploaded = assets / f"item_{item['id']}.webp"
            art = uploaded if uploaded.is_file() else studio.STATIC / CHANNEL_ART[item['channel_id']]
            if not art.is_file():
                raise ValueError('Lipseste imaginea personajului')
            composition = work / 'index.html'
            composition.write_text(_html(item, job['duration_seconds'], art), encoding='utf-8')
            output = work / 'hyperframes-concept.mp4'
            command = [executable, 'render', '-c', str(composition), '-o', str(output), '--fps', '12']
            if Path(executable).suffix.lower() in ('.js', '.mjs'):
                node = shutil.which('node')
                if not node:
                    raise ValueError('Node.js nu este instalat')
                command.insert(0, node)
            env = os.environ.copy()
            env['DO_NOT_TRACK'] = '1'
            env['NO_UPDATE_NOTIFIER'] = '1'
            # Only an explicit local CLI render; never invoke publish/auth/cloud.
            proc = subprocess.run(command, cwd=str(work), env=env,
                                  capture_output=True, text=True,
                                  timeout=max(180, job['duration_seconds'] * 12), check=False)
            if proc.returncode != 0 or not output.is_file() or output.stat().st_size < 1024:
                raise RuntimeError('HyperFrames render nereusit: ' + (proc.stderr or '')[-350:])
            destination = assets / f"item_{item['id']}_video.mp4"
            assets.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(output, destination)
            (assets / f"item_{item['id']}_video_source.json").write_text(
                json.dumps({'engine': 'HYPERFRAMES_LOCAL_CONCEPT', 'ai_3d': False,
                            'published': False, 'duration_seconds': job['duration_seconds']},
                           ensure_ascii=False), encoding='utf-8')
            _set(job_id, 'DONE', output=str(output))
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
            _set(job_id, 'FAILED', error=str(exc)[:400])


def output_file(job_id: int) -> Path | None:
    row = db.one_row('SELECT status,output_path FROM hyperframes_jobs WHERE id=?', (job_id,))
    if not row or row['status'] != 'DONE' or not row['output_path']:
        return None
    root = Path(os.getenv('BERRY_OUTPUT_DIR', str(studio.OUTPUT_ROOT))).resolve()
    target = Path(row['output_path']).resolve()
    if target.parent != root / f'hyperframes_{job_id:06d}' or target.name != 'hyperframes-concept.mp4':
        return None
    return target if target.is_file() else None
