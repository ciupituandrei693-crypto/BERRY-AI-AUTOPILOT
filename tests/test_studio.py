"""Local-only media assembly tests. Never contact external services."""
import time

import pytest
from fastapi.testclient import TestClient
from berry import db, studio
from berry.app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'DB', tmp_path / 'berry_test.sqlite3')
    monkeypatch.setenv('BERRY_OUTPUT_DIR', str(tmp_path / 'outputs'))
    monkeypatch.setenv('BERRY_PREVIEW_MAX_SECONDS', '2')
    monkeypatch.delenv('BERRY_PIPER_MODEL', raising=False)
    with TestClient(app) as c:
        yield c


def wait_job(client, job_id, timeout=20):
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        r = client.get(f'/api/studio/jobs/{job_id}')
        if r.json()['status'] not in ('QUEUED', 'RUNNING'):
            return r.json()
        time.sleep(.1)
    pytest.fail('Local render did not finish')


def test_capabilities_are_local_and_no_cloud(client):
    r = client.get('/api/studio/capabilities')
    assert r.status_code == 200
    body = r.json()
    assert body['local_only'] and not body['social_posting'] and not body['cloud_gpu']
    assert body['render_kind'] == 'STATIC_CONCEPT_STORYBOARD'
    assert body['components']['external_social']['ready'] is False


def test_render_package_without_ffmpeg(client, tmp_path, monkeypatch):
    original = studio.binary_path
    monkeypatch.setattr(studio, 'binary_path', lambda name, env: None if name in ('ffmpeg','piper') else original(name,env))
    item_id = client.post('/api/items', json={
        'channel_id':'lab', 'content_type':'main90', 'topic':'De ce stelele strălucesc'
    }).json()['id']
    r = client.post('/api/studio/render', json={'item_id':item_id,'mode':'preview'})
    assert r.status_code == 202
    job = wait_job(client, r.json()['job_id'])
    assert job['status'] == 'PACKAGE_ONLY'
    assert job['result']['video_created'] is False
    assert job['result']['ai_animated'] is False
    assert job['result']['target_duration_seconds'] == 90
    assert client.get(f"/api/studio/jobs/{job['id']}/file/script").status_code == 200
    assert 'AFINA' in client.get(f"/api/studio/jobs/{job['id']}/file/script").text
    assert client.get(f"/api/studio/jobs/{job['id']}/file/subtitles").status_code == 200
    assert client.get(f"/api/studio/jobs/{job['id']}/file/video").status_code == 404
    assert client.get(f"/api/studio/jobs/{job['id']}/file/image").status_code == 200
    assert client.get('/api/items').json()[0]['status'] == 'DRAFT'


def test_reject_invalid_or_approved_render(client):
    assert client.post('/api/studio/render',json={'item_id':999}).status_code == 404
    assert client.post('/api/studio/render',json={'item_id':1,'mode':'publish'}).status_code == 422
    item_id = client.post('/api/items',json={
        'channel_id':'beats','content_type':'short15','topic':'Cântec original despre speranță'
    }).json()['id']
    batch = client.post('/api/batches',json={'name':'Batch de test','item_ids':[item_id]}).json()
    client.post(f"/api/batches/{batch['id']}/approve")
    assert client.post('/api/studio/render',json={'item_id':item_id}).status_code == 409
    assert client.get('/api/studio/jobs/9999/file/manifest').status_code == 404


@pytest.mark.skipif(not studio.binary_path('ffmpeg','BERRY_FFMPEG_PATH'),reason='FFmpeg not installed')
def test_real_ffmpeg_static_preview(client):
    item_id = client.post('/api/items',json={
        'channel_id':'wealth','content_type':'short15','topic':'Fondul de urgență'
    }).json()['id']
    r=client.post('/api/studio/render',json={'item_id':item_id,'mode':'preview'})
    job=wait_job(client,r.json()['job_id'],timeout=30)
    assert job['status'] == 'DONE',job['error']
    assert job['result']['rendered_duration_seconds'] == 2
    assert job['result']['ai_animated'] is False
    video=client.get(f"/api/studio/jobs/{job['id']}/file/video")
    assert video.status_code == 200
    assert len(video.content) > 1000
