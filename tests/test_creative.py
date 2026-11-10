"""Mocked local engine integration tests; never require AI models or network."""
import io
import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from berry import creative, db, engines
from berry.app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'DB', tmp_path / 'test.sqlite3')
    monkeypatch.setenv('BERRY_ASSET_DIR', str(tmp_path / 'assets'))
    monkeypatch.setenv('BERRY_OUTPUT_DIR', str(tmp_path / 'outputs'))
    monkeypatch.setenv('BERRY_SCRIPT_DIR', str(tmp_path / 'scripts'))
    with TestClient(app) as c:
        yield c


def item(client, channel='lab', content_type='image'):
    return client.post('/api/items', json={'channel_id':channel,'content_type':content_type,
         'topic':'Cercetăm lumina și stelele'}).json()['id']


def wait(client, job_id):
    for _ in range(100):
        rows = client.get('/api/ai/jobs').json()
        found = next(x for x in rows if x['id']==job_id)
        if found['status'] not in ('QUEUED','RUNNING'):
            return found
        time.sleep(.05)
    pytest.fail('AI mock job timeout')


def test_external_urls_rejected(monkeypatch):
    monkeypatch.setenv('BERRY_COMFYUI_URL','https://evil.example:443')
    with pytest.raises(engines.EngineError):
        engines.local_base('comfyui')
    monkeypatch.setenv('BERRY_COMFYUI_URL','http://127.0.0.1:8188@evil.example:8188')
    with pytest.raises(engines.EngineError):
        engines.local_base('comfyui')
    monkeypatch.setenv('BERRY_COMFYUI_URL','http://127.0.0.1:8188')
    assert engines.local_base('comfyui') == 'http://127.0.0.1:8188'


def test_engine_endpoint_offline_and_invalid_job(client, monkeypatch):
    monkeypatch.setattr(engines,'statuses',lambda: {'comfyui':{'ready':False}})
    i=item(client)
    r=client.post('/api/ai/jobs',json={'item_id':i,'engine':'comfyui'})
    assert r.status_code==409
    assert client.post('/api/ai/jobs',json={'item_id':i,'engine':'cloud_gpu'}).status_code==422


def test_comfyui_api_image_adapter(client, tmp_path, monkeypatch):
    workflow=tmp_path/'workflow.json'
    workflow.write_text(json.dumps({'1':{'class_type':'CLIPTextEncode','inputs':{'text':'{{PROMPT}}'}},
        '2':{'class_type':'KSampler','inputs':{'seed':'{{SEED}}'}}}),encoding='utf-8')
    monkeypatch.setenv('BERRY_COMFYUI_WORKFLOW',str(workflow))
    monkeypatch.setattr(engines,'statuses',lambda: {'comfyui':{'ready':True}})
    def fake_json(engine,path,**kwargs):
        if path=='/prompt':
            assert 'Cinematic 3D' in kwargs['payload']['prompt']['1']['inputs']['text']
            assert isinstance(kwargs['payload']['prompt']['2']['inputs']['seed'],int)
            return {'prompt_id':'mock-123'}
        if path=='/history/mock-123':
            return {'mock-123':{'outputs':{'9':{'images':[{'filename':'test.png','subfolder':'','type':'output'}]}}}}
        raise AssertionError(path)
    def fake_image(engine,path,**kwargs):
        assert path.startswith('/view?')
        image=Image.new('RGB',(32,64),'#335577')
        output=io.BytesIO();image.save(output,'PNG');return output.getvalue()
    monkeypatch.setattr(engines,'json_request',fake_json)
    monkeypatch.setattr(engines,'request',fake_image)
    i=item(client)
    r=client.post('/api/ai/jobs',json={'item_id':i,'engine':'comfyui'})
    assert r.status_code==202
    result=wait(client,r.json()['job_id'])
    assert result['status']=='DONE',result
    assert (tmp_path/'assets'/f'item_{i}.webp').is_file()
    assert result['result']['published'] is False


def test_ace_step_music_adapter(client, tmp_path, monkeypatch):
    monkeypatch.setattr(engines,'statuses',lambda: {'ace_step':{'ready':True}})
    def fake_json(engine,path,**kwargs):
        if path=='/release_task':
            assert kwargs['payload']['task_type']=='text2music'
            return {'data':{'task_id':'music-123'}}
        if path=='/query_result':
            return {'data':[{'status':1,'result':json.dumps([{'file':'/tmp/test.wav'}])}]}
        raise AssertionError(path)
    monkeypatch.setattr(engines,'json_request',fake_json)
    monkeypatch.setattr(engines,'request',lambda *a,**k: b'RIFF'+b'\x00'*4+b'WAVE'+b'\x00'*64)
    i=item(client,channel='beats',content_type='short15')
    r=client.post('/api/ai/jobs',json={'item_id':i,'engine':'ace_step'})
    assert r.status_code==202
    result=wait(client,r.json()['job_id'])
    assert result['status']=='DONE',result
    assert (tmp_path/'assets'/f'item_{i}_soundtrack.wav').is_file()


def test_voice_and_analytics_import(client, tmp_path):
    i=item(client,content_type='short15')
    r=client.post(f'/api/items/{i}/voice',files={'file':('test.wav',b'RIFF'+b'\0'*4+b'WAVE'+b'\0'*32,'audio/wav')})
    assert r.status_code==200
    assert (tmp_path/'assets'/f'item_{i}_voice.wav').is_file()
    csvdata=('platform,channel_id,title,views,likes,comments,shares,watch_seconds,published_at\n'
             'youtube,lab,Experimente,1000,70,12,8,600,2026-10-15T10:00:00+02:00\n').encode()
    response=client.post('/api/analytics/import',files={'file':('stats.csv',csvdata,'text/csv')})
    assert response.status_code==200,response.text
    assert response.json()['imported']==1
    assert client.post('/api/analytics/import',files={'file':('stats.csv',csvdata,'text/csv')}).json()['duplicates']==1
    report=client.get('/api/analytics').json()
    assert report['channels'][0]['engagement_percent']==9.0
    assert report['platform_connected'] is False

@pytest.mark.skipif(not __import__('shutil').which('ffmpeg'), reason='FFmpeg not installed')
def test_imported_video_and_voice_mixing(client, tmp_path):
    import subprocess
    import wave
    source = tmp_path / 'clip.mp4'
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',
                    '-f','lavfi','-i','color=c=blue:s=160x288:r=12',
                    '-t','1','-c:v','libx264','-pix_fmt','yuv420p',str(source)],
                   check=True,timeout=30)
    voice = io.BytesIO()
    with wave.open(voice,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000)
        w.writeframes(b'\x00\x00'*16000)
    i = item(client, content_type='short15')
    v = client.post(f'/api/items/{i}/video',files={'file':('clip.mp4',source.read_bytes(),'video/mp4')})
    assert v.status_code==200,v.text
    a = client.post(f'/api/items/{i}/voice',files={'file':('voice.wav',voice.getvalue(),'audio/wav')})
    assert a.status_code==200,a.text
    r = client.post('/api/studio/render',json={'item_id':i,'mode':'full'})
    assert r.status_code==202,r.text
    from tests.test_studio import wait_job
    job=wait_job(client,r.json()['job_id'],timeout=30)
    assert job['status']=='DONE',job['error']
    assert job['result']['render_kind']=='IMPORTED_OR_GENERATED_LOCAL_VIDEO'
    assert job['result']['rendered_duration_seconds'] <= 2
    assert job['result']['audio_source']=='VOICE'
    assert client.get(f"/api/studio/jobs/{job['id']}/file/video").status_code==200
    report=client.get(f'/api/qa/{i}').json()['report']
    assert any('Durata MP4' in reason for reason in report['reasons'])


def test_voice_studio_local_tts_adapter(client, tmp_path, monkeypatch):
    monkeypatch.setattr(engines,'statuses',lambda: {'voice_studio':{'ready':True}})
    def fake_voice(engine,path,**kwargs):
        assert engine=='voice_studio' and path=='/v1/audio/speech'
        assert kwargs['payload']['response_format']=='wav'
        return b'RIFF'+b'\0'*4+b'WAVE'+b'\0'*100
    monkeypatch.setattr(engines,'request',fake_voice)
    i=item(client,content_type='short15')
    r=client.post('/api/ai/jobs',json={'item_id':i,'engine':'voice_studio'})
    assert r.status_code==202
    j=wait(client,r.json()['job_id'])
    assert j['status']=='DONE',j
    assert (tmp_path/'assets'/f'item_{i}_voice.wav').is_file()
