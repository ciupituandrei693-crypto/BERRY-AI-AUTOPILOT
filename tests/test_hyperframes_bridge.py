"""Local HyperFrames bridge tests, with mocked CLI; no external process launched."""
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from berry import db, hyperframes_bridge as hf, studio
from berry.app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'DB', tmp_path / 'berry.sqlite3')
    monkeypatch.setenv('BERRY_OUTPUT_DIR', str(tmp_path / 'outputs'))
    monkeypatch.setenv('BERRY_ASSET_DIR', str(tmp_path / 'assets'))
    monkeypatch.delenv('BERRY_HYPERFRAMES_BIN', raising=False)
    with TestClient(app) as c:
        yield c


def new_item(client):
    r = client.post('/api/items', json={'channel_id': 'lab',
                    'content_type': 'short15', 'topic': 'AFINA explica gravitatia'})
    assert r.status_code == 201
    return r.json()['id']


def test_render_requires_installed_cli(client):
    item_id = new_item(client)
    assert client.get('/api/studio/hyperframes/status').json()['ready_for_local_render'] is False
    assert client.post('/api/studio/hyperframes/render',
                       json={'item_id': item_id}).status_code == 409


def test_offline_composition_escapes_html(tmp_path):
    art = tmp_path / 'fruit.png'
    art.write_bytes(b'\x89PNG\r\n\x1a\nsample')
    content = hf._html({'title': '<script>alert(1)</script>',
                        'topic': '<img src=x onerror=alert(1)>',
                        'channel_id': 'lab'}, 15, art)
    assert '<script>alert(1)</script>' not in content
    assert '&lt;script&gt;' in content
    assert '&lt;img' in content
    assert 'https://' not in content
    assert 'data-duration="15"' in content


def test_mocked_cli_creates_local_concept_not_ai(client, tmp_path, monkeypatch):
    item_id = new_item(client)
    cli = tmp_path / 'hyperframes.cmd'
    cli.write_text('mock')
    monkeypatch.setenv('BERRY_HYPERFRAMES_BIN', str(cli))
    gsap = tmp_path / 'gsap.min.js'
    gsap.write_text('window.gsap = {};', encoding='utf8')
    monkeypatch.setenv('BERRY_HYPERFRAMES_GSAP_PATH', str(gsap))
    # Avoid starting background thread; insert a job and run its worker inline.
    now = db.utcnow()
    with db.connection() as con:
        job_id = con.execute('''INSERT INTO hyperframes_jobs(item_id,duration_seconds,created_at,updated_at)
                                VALUES(?,?,?,?)''', (item_id, 15, now, now)).lastrowid

    def fake_run(args, **kwargs):
        assert args[1] == 'render'
        assert '-o' in args
        output = Path(args[args.index('-o')+1])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b'\0' * 2048)
        return subprocess.CompletedProcess(args, 0, '', '')
    monkeypatch.setattr(hf.subprocess, 'run', fake_run)
    hf._worker(job_id, str(cli))
    assert hf._job(job_id)['status'] == 'DONE'
    assert hf.output_file(job_id).is_file()
    assert client.get(f'/api/studio/hyperframes/jobs/{job_id}/video').status_code == 200
    assets = tmp_path / 'assets'
    assert (assets / f'item_{item_id}_video.mp4').is_file()
    assert studio._verified_ai_video_flag(assets / f'item_{item_id}_video_source.json') is False
