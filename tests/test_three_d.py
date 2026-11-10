"""3D integration contract tests; Blender hardware render requires Windows test."""
import json
import math
import time
import wave
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from berry import db, studio, three_d, engines
from berry.app import app


def wav_file(path: Path, seconds=0.5):
    import struct
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        samples = [round(9000 * math.sin(2 * math.pi * 220 * i / 16000)) for i in range(round(16000 * seconds))]
        w.writeframes(struct.pack('<' + 'h' * len(samples), *samples))
    return path


def test_audio_energy_fallback(tmp_path):
    f = wav_file(tmp_path / 'voice.wav')
    cues = three_d._energy_cues(f, .5)
    assert cues and all(c['value'] in ('X','A','D') for c in cues)
    assert cues[-1]['end'] <= .5


def test_rhubarb_cues_validation():
    assert three_d._validate_cues([{'start':0, 'end':.2, 'value':'A'}], 1)[0]['value'] == 'A'
    with pytest.raises(ValueError):
        three_d._validate_cues([{'start':0, 'end':2, 'value':'COMMAND'}], 2)
    with pytest.raises(ValueError):
        three_d._validate_cues([{'start':float('nan'), 'end':2, 'value':'A'}], 2)
    with pytest.raises(ValueError):
        three_d._validate_cues([{'start':1, 'end':.2, 'value':'A'}], 2)


def test_no_audio_no_lipsync(tmp_path):
    assert three_d.mouth_cues(None, tmp_path, 5) == ([], 'NO_VOICE_NO_LIPSYNC')


def test_procedural_3d_job_mocked_blender(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'DB', tmp_path / 'test.sqlite3')
    monkeypatch.setenv('BERRY_ASSET_DIR', str(tmp_path / 'assets'))
    monkeypatch.setenv('BERRY_OUTPUT_DIR', str(tmp_path / 'outputs'))
    monkeypatch.setenv('BERRY_3D_MAX_SECONDS', '2')
    monkeypatch.setattr(engines, 'statuses', lambda: {'blender_3d': {'ready': True}})
    original_binary = studio.binary_path
    monkeypatch.setattr(studio, 'binary_path', lambda name, env: '/fake/blender' if name == 'blender' else (None if name == 'ffmpeg' else original_binary(name, env)))
    def fake_run(args, timeout):
        assert '--factory-startup' in args
        config = json.loads(Path(args[-1]).read_text(encoding='utf-8'))
        assert config['duration'] == 2
        assert config['channel'] == 'lab'
        Path(config['output']).write_bytes(b'fake-mp4-' * 300)
        Path(config['blend']).write_bytes(b'BLENDER' * 300)
        from subprocess import CompletedProcess
        return CompletedProcess(args, 0, '', '')
    monkeypatch.setattr(three_d, '_run', fake_run)
    with TestClient(app) as client:
        item_id = client.post('/api/items', json={'channel_id':'lab','content_type':'short15',
            'topic':'Testăm personajul AFINA în laborator'}).json()['id']
        r = client.post('/api/ai/jobs', json={'item_id': item_id, 'engine':'blender_3d'})
        assert r.status_code == 202, r.text
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            job = next(x for x in client.get('/api/ai/jobs').json() if x['id'] == r.json()['job_id'])
            if job['status'] not in ('QUEUED','RUNNING'):
                break
            time.sleep(.03)
        assert job['status'] == 'DONE', job
        assert job['result']['rigging'] == 'ARMATURE_AND_SHAPE_KEYS'
        assert job['result']['model_benchmark_on_this_pc'] is False
        assert (tmp_path/'assets'/f'item_{item_id}_video.mp4').is_file()
        assert (tmp_path/'outputs'/f'rig3d_{job["id"]:06d}'/'rigged_character.blend').is_file()
        report = client.get('/api/local/diagnostics').json()
        assert report['local_only'] is True and report['models_benchmarked'] is False
        assert client.post('/api/ai/jobs', json={'item_id': item_id, 'engine':'cloud_gpu'}).status_code == 422
