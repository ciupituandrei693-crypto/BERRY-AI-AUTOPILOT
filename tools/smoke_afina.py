"""End-to-end AFINA FRUIT LAB 15-second LOCAL smoke test.

Uses an isolated temporary database/output. Never touches real projects, accounts,
cloud, or social publishing. Produces motion graphics (not AI 3D video).
"""
from __future__ import annotations

import json
import os
import tempfile
import time
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from berry import db, seo, studio
    if not studio.binary_path('ffmpeg', 'BERRY_FFMPEG_PATH'):
        print(json.dumps({'status': 'SKIP', 'reason': 'FFmpeg unavailable'}))
        return 2
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='berry-afina-e2e-') as folder:
        root = Path(folder)
        db.DB = root / 'berry-smoke.sqlite3'
        os.environ['BERRY_OUTPUT_DIR'] = str(root / 'outputs')
        os.environ['BERRY_ASSET_DIR'] = str(root / 'assets')
        os.environ['BERRY_SCRIPT_DIR'] = str(root / 'scripts')
        os.environ['BERRY_SAPI_TTS'] = 'false'
        db.init_db()
        studio.init_jobs()
        now = db.utcnow()
        topic = 'AFINA explica de ce pluteste gheata pe apa'
        with db.connection() as con:
            cur = con.execute('''INSERT INTO items
                (channel_id,content_type,topic,title,seo_json,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?)''',
                ('lab', 'short15', topic, 'AFINA explica gheata pe apa',
                 json.dumps(seo.draft('lab', topic, 'short15'), ensure_ascii=False), now, now))
            item_id = cur.lastrowid
        job_id = studio.submit(item_id, 'full')
        deadline = time.monotonic() + 240
        job = None
        while time.monotonic() < deadline:
            job = studio.get_job(job_id)
            if job and job['status'] not in ('QUEUED', 'RUNNING'):
                break
            time.sleep(.3)
        if not job or job['status'] in ('QUEUED', 'RUNNING'):
            print(json.dumps({'status': 'FAIL', 'reason': 'Timeout 240s'}))
            return 1
        video = studio.output_file(job_id, 'video')
        result = job.get('result') or {}
        success = (job['status'] == 'DONE' and video is not None and
                   video.is_file() and video.stat().st_size > 1024 and
                   result.get('target_duration_seconds') == 15 and
                   result.get('video_created') is True and
                   result.get('published') is False and
                   result.get('qa_approved') is False)
        print(json.dumps({
            'status': 'PASS' if success else 'FAIL',
            'channel': 'lab', 'character': 'AFINA', 'seconds': 15,
            'job_status': job['status'], 'render_kind': result.get('render_kind'),
            'ai_3d_generated': result.get('ai_animated', False),
            'video_created': bool(video and video.is_file()),
            'published': False, 'cloud_used': False,
            'elapsed_seconds': round(time.monotonic()-started, 2),
            'note': 'Temp files deleted after smoke test; no account or external action',
        }, ensure_ascii=False))
        return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
