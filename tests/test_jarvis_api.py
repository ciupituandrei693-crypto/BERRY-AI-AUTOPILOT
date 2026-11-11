"""JARVIS ONE local integration tests; no remote calls, no cloud, no publishing."""
from fastapi.testclient import TestClient
import pytest
from berry import db
from berry.app import app

KEY = 'local-jarvis-secret-0123456789-ABCDEFGHIJKLMNOPQRSTUVWXYZ'


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'DB', tmp_path / 'jarvis.sqlite3')
    monkeypatch.setenv('BERRY_JARVIS_API_KEY', KEY)
    with TestClient(app) as c:
        yield c


def headers():
    return {'X-JARVIS-KEY': KEY}


def payload():
    return {'request_id': 'afina-lab-2026-11-11-001',
            'channel_id': 'lab', 'content_type': 'short15',
            'topic': 'cum functioneaza gravitatia'}


def test_jarvis_key_is_required(client):
    assert client.get('/api/v1/jarvis/capabilities').status_code == 401
    assert client.get('/api/v1/jarvis/capabilities', headers={'X-JARVIS-KEY': 'bad'}).status_code == 401
    r = client.get('/api/v1/jarvis/capabilities', headers=headers())
    assert r.status_code == 200
    assert r.json()['assistant'] == 'JARVIS_ONE_ULTIMATE'
    assert r.json()['social_publishing'] is False
    assert r.json()['cloud_gpu'] is False


def test_jarvis_key_must_be_configured(client, monkeypatch):
    monkeypatch.delenv('BERRY_JARVIS_API_KEY')
    assert client.get('/api/v1/jarvis/capabilities', headers=headers()).status_code == 503


def test_create_idempotent_and_review_without_approval(client):
    a = client.post('/api/v1/jarvis/packages', headers=headers(), json=payload())
    assert a.status_code == 201, a.text
    item = a.json()
    assert item['item_status'] == 'DRAFT'
    assert item['external_cost_usd'] == 0
    b = client.post('/api/v1/jarvis/packages', headers=headers(), json=payload())
    assert b.status_code == 201
    assert b.json()['id'] == item['id']
    assert len(client.get('/api/items').json()) == 1
    conflict = {**payload(), 'topic': 'alt subiect'}
    assert client.post('/api/v1/jarvis/packages', headers=headers(), json=conflict).status_code == 409
    pkg_id = item['id']
    q = client.get(f'/api/v1/jarvis/packages/{pkg_id}/qa', headers=headers())
    assert q.status_code == 200 and q.json()['passed'] is False
    review = client.post(f'/api/v1/jarvis/packages/{pkg_id}/review-request', headers=headers())
    assert review.status_code == 200
    assert review.json()['approved'] is False
    assert client.get(f'/api/v1/jarvis/packages/{pkg_id}/events', headers=headers()).json()[-1]['kind'] == 'HUMAN_REVIEW_REQUESTED'
    assert client.post(f'/api/v1/jarvis/packages/{pkg_id}/approve', headers=headers()).status_code == 423
    assert client.post(f'/api/v1/jarvis/packages/{pkg_id}/publish', headers=headers()).status_code == 423
    assert client.post('/api/v1/jarvis/cloud/activate', headers=headers()).status_code == 423
    assert client.get(f'/api/v1/jarvis/packages/{pkg_id}', headers=headers()).json()['published'] is False


def test_jarvis_cors_origin_and_validation(client):
    assert client.post('/api/v1/jarvis/packages', headers={**headers(), 'Origin': 'https://evil.example'},
                       json=payload()).status_code == 403
    assert client.post('/api/v1/jarvis/packages', headers=headers(),
                       json={**payload(), 'channel_id': 'unknown'}).status_code == 422
    assert client.get('/api/v1/jarvis/packages/99999', headers=headers()).status_code == 404
