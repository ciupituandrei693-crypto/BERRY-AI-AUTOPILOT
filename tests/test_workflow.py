"""End-to-end local production checks; no external calls or spending."""
from __future__ import annotations
import io
import os
import time
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from berry import db, studio
from berry.app import app

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'DB', tmp_path / 'db.sqlite3')
    monkeypatch.setenv('BERRY_OUTPUT_DIR', str(tmp_path / 'outputs'))
    monkeypatch.setenv('BERRY_ASSET_DIR', str(tmp_path / 'assets'))
    monkeypatch.setenv('BERRY_SCRIPT_DIR', str(tmp_path / 'scripts'))
    monkeypatch.delenv('BERRY_PIPER_MODEL', raising=False)
    with TestClient(app) as c:
        yield c


def make_item(client, channel='lab', content_type='short15'):
    r = client.post('/api/items', json={'channel_id':channel,'content_type':content_type,
                'topic':'De ce strălucesc stelele în fiecare noapte?'})
    assert r.status_code == 201, r.text
    return r.json()['id']


def wait(client, job_id):
    for _ in range(180):
        j = client.get(f'/api/studio/jobs/{job_id}').json()
        if j['status'] not in ('QUEUED', 'RUNNING'):
            return j
        time.sleep(.15)
    pytest.fail('Render timeout')


def flags(client, item_id):
    data={k:True for k in ('facts_checked','visual_rights','voice_rights','music_rights','disclosure_checked')}
    r=client.post(f'/api/qa/{item_id}/checks',json={**data,'notes':'Drepturi confirmate de autor'})
    assert r.status_code == 200, r.text


def test_quality_requires_full_render_and_manual_rights(client):
    item_id = make_item(client)
    r=client.get(f'/api/qa/{item_id}').json()
    assert not r['report']['passed']
    assert any('FULL' in x for x in r['report']['reasons'])
    flags(client, item_id)
    assert not client.post(f'/api/qa/{item_id}/run').json()['passed']
    batch = client.post('/api/batches',json={'name':'Aprobări editoriale','item_ids':[item_id]}).json()
    assert client.post(f"/api/batches/{batch['id']}/approve").status_code == 200
    when=(datetime.now(timezone.utc)+timedelta(days=2)).isoformat()
    r=client.post('/api/calendar',json={'item_id':item_id,'platform':'youtube','scheduled_at':when})
    assert r.status_code == 409
    assert 'QA' in r.json()['detail']


@pytest.mark.skipif(not studio.binary_path('ffmpeg','BERRY_FFMPEG_PATH'),reason='FFmpeg unavailable')
def test_full_render_qa_approval_schedule_export(client):
    item_id=make_item(client)
    flags(client,item_id)
    r=client.post('/api/studio/render',json={'item_id':item_id,'mode':'full'})
    assert r.status_code==202,r.text
    job=wait(client,r.json()['job_id'])
    assert job['status']=='DONE',job['error']
    assert job['result']['render_kind']=='MOTION_GRAPHICS_LOCAL'
    assert job['result']['rendered_duration_seconds']==15
    video=client.get(f"/api/studio/jobs/{job['id']}/file/video")
    assert video.status_code==200 and len(video.content)>5000
    qa=client.post(f'/api/qa/{item_id}/run').json()
    assert qa['passed'],qa['reasons']
    assert 'animație 3D AI' in ' '.join(qa['warnings'])
    batch=client.post('/api/batches',json={'name':'Lot aprobat pentru export','item_ids':[item_id]}).json()
    assert client.post(f"/api/batches/{batch['id']}/approve").status_code==200
    when=(datetime.now(timezone.utc)+timedelta(days=3)).isoformat()
    sched=client.post('/api/calendar',json={'item_id':item_id,'platform':'youtube','scheduled_at':when})
    assert sched.status_code==201,sched.text
    sid=sched.json()['id']
    pkg=client.get(f'/api/calendar/{sid}/package')
    assert pkg.status_code==200
    with zipfile.ZipFile(io.BytesIO(pkg.content)) as z:
        names=z.namelist()
        assert 'motion-video.mp4' in names
        assert 'SEO_AND_CAPTIONS.json' in names
        assert 'QA_REPORT.json' in names
        assert b'"published": false' in z.read('SEO_AND_CAPTIONS.json')
    assert client.get('/api/calendar').json()[0]['status']=='EXPORTED_LOCAL'
    assert client.post(f'/api/qa/{item_id}/checks',json={}).status_code==409


def test_backup_and_host_origin_security(client):
    make_item(client)
    backup=client.get('/api/backup')
    assert backup.status_code==200
    with zipfile.ZipFile(io.BytesIO(backup.content)) as z:
        assert 'berry.sqlite3' in z.namelist()
        assert z.read('berry.sqlite3').startswith(b'SQLite format 3')
    r=client.post('/api/items',headers={'origin':'https://evil.example'},json={'channel_id':'lab','content_type':'image','topic':'test image'})
    assert r.status_code==403
    r=client.get('/api/status',headers={'host':'evil.example'})
    assert r.status_code==400


def test_user_art_upload_and_image_qa(client):
    item_id=make_item(client,content_type='image')
    img=Image.new('RGB',(100,100),'purple')
    b=io.BytesIO();img.save(b,format='PNG')
    r=client.post(f'/api/items/{item_id}/art',files={'file':('scene.png',b.getvalue(),'image/png')})
    assert r.status_code==200,r.text
    assert r.json()['source']=='USER_SUPPLIED'
    flags(client,item_id)
    r=client.post('/api/studio/render',json={'item_id':item_id,'mode':'full'})
    job=wait(client,r.json()['job_id'])
    assert job['status']=='DONE',job['error']
    assert job['result']['art_source']=='USER_SUPPLIED'
    assert client.post(f'/api/qa/{item_id}/run').json()['passed']
    assert client.get(f"/api/studio/jobs/{job['id']}/file/image").status_code==200


def test_beats_requires_original_track(client):
    item_id=make_item(client,channel='beats',content_type='image')
    flags(client,item_id)
    assert not client.get(f'/api/qa/{item_id}').json()['report']['passed']
    assert client.post(f'/api/items/{item_id}/soundtrack',files={'file':('bad.mp3',b'not an mp3','audio/mpeg')}).status_code==422


def test_script_edit_invalidates_existing_render(client):
    item_id=make_item(client,content_type='image')
    original=client.get(f'/api/items/{item_id}/script').json()
    assert not original['custom']
    edited='Scena de deschidere despre stele.\nScena finală cu concluzii prudente.'
    r=client.post(f'/api/items/{item_id}/script',json={'text':edited})
    assert r.status_code==200,r.text
    assert client.get(f'/api/items/{item_id}/script').json()['text'].strip()==edited
    job_id=client.post('/api/studio/render',json={'item_id':item_id,'mode':'full'}).json()['job_id']
    assert wait(client,job_id)['status']=='DONE'
    r=client.post(f'/api/items/{item_id}/script',json={'text':edited+'\nO linie nouă.'})
    assert r.status_code==200
    assert client.get(f'/api/studio/jobs/{job_id}').json()['status']=='STALE'
    assert client.get(f'/api/qa/{item_id}').json()['report']['passed'] is False


def test_one_click_local_production_for_image(client):
    item_id=make_item(client,content_type='image')
    r=client.post('/api/production/start')
    assert r.status_code==202,r.text
    run_id=r.json()['run_id']
    for _ in range(100):
        runs=client.get('/api/production/runs').json()
        if runs and runs[0]['status'] not in ('QUEUED','RUNNING'):
            break
        time.sleep(.1)
    assert runs[0]['status']=='FINISHED',runs
    assert runs[0]['total']==1 and runs[0]['failed']==0
    assert client.get('/api/production/summary').json()['local_only'] is True
