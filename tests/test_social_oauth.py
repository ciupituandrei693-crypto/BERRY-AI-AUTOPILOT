"""OAuth tests are offline: no Google, Meta or TikTok network traffic."""
import json
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient

from berry import db, social_oauth
from berry.app import app

BERRY_KEY = 'berry-private-local-access-key-123456'


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'DB', tmp_path / 'social.sqlite3')
    monkeypatch.setenv('LOCALAPPDATA', str(tmp_path / 'appdata'))
    monkeypatch.setenv('BERRY_ACCESS_KEY', BERRY_KEY)
    monkeypatch.setenv('BERRY_SOCIAL_OAUTH_ENABLED', 'true')
    monkeypatch.setenv('BERRY_GOOGLE_OAUTH_CLIENT_ID', 'example.apps.googleusercontent.com')
    secret = tmp_path / 'google.json'
    secret.write_text(json.dumps({'web': {'client_secret': 'very-private-secret'}}))
    monkeypatch.setenv('BERRY_GOOGLE_OAUTH_CLIENT_SECRET_FILE', str(secret))
    monkeypatch.delenv('BERRY_SOCIAL_REDIRECT_BASE', raising=False)
    with TestClient(app) as c:
        yield c


def headers():
    return {'X-BERRY-KEY': BERRY_KEY}


def test_status_never_leaks_credentials(client):
    assert client.get('/api/social/status').status_code == 401
    r = client.get('/api/social/status', headers=headers())
    assert r.status_code == 200
    assert r.json()['providers']['youtube']['configured'] is True
    assert r.json()['providers']['tiktok']['redirect_ready'] is False
    assert r.json()['publishing_enabled'] is False
    assert 'very-private-secret' not in r.text


def test_explicit_oauth_state_encryption_and_replay(client, monkeypatch):
    def fake_exchange(provider, code, redirect, verifier):
        assert provider == 'youtube'
        assert code == 'demo-auth-code'
        assert redirect == 'http://localhost:8765/api/social/youtube/callback'
        assert len(verifier) > 40
        return {'access_token': 'private-access-token', 'refresh_token': 'private-refresh'}, 'UC' + 'A'*22, 'Fruit Lab'
    monkeypatch.setattr(social_oauth, '_exchange', fake_exchange)
    start = client.post('/api/social/youtube/start', headers=headers(), json={'channel_id': 'lab'})
    assert start.status_code == 200, start.text
    result = start.json()
    assert result['publishing_enabled'] is False
    url = urlsplit(result['authorization_url'])
    query = parse_qs(url.query)
    assert url.hostname == 'accounts.google.com'
    assert query['scope'] == [social_oauth.SCOPE['youtube']]
    assert query['code_challenge_method'] == ['S256']
    assert 'youtube.upload' not in result['authorization_url']
    state = query['state'][0]
    callback = client.get('/api/social/youtube/callback',
                          params={'code': 'demo-auth-code', 'state': state},
                          follow_redirects=False)
    assert callback.status_code == 303
    assert callback.headers['location'] == '/?oauth=connected'
    accounts = client.get('/api/social/status', headers=headers()).json()['providers']['youtube']['connected']
    assert accounts[0]['display_name'] == 'Fruit Lab'
    assert 'private-access-token' not in str(accounts)
    dbrow = db.one_row('SELECT token_cipher FROM social_accounts')
    assert 'private-access-token' not in dbrow['token_cipher']
    assert json.loads(social_oauth._fernet().decrypt(dbrow['token_cipher'].encode()))['refresh_token'] == 'private-refresh'
    again = client.get('/api/social/youtube/callback',
                       params={'code': 'demo-auth-code', 'state': state}, follow_redirects=False)
    assert again.headers['location'] == '/?oauth=failed'
    disconnect = client.post('/api/social/youtube/disconnect', headers=headers(),
                             json={'channel_id': 'lab'})
    assert disconnect.status_code == 200
    assert disconnect.json()['remote_token_revoked'] is False
    assert not client.get('/api/social/status', headers=headers()).json()['providers']['youtube']['connected']


def test_opt_in_is_disabled_by_default(client, monkeypatch):
    monkeypatch.delenv('BERRY_SOCIAL_OAUTH_ENABLED')
    assert client.post('/api/social/youtube/start', headers=headers(),
                       json={'channel_id': 'lab'}).status_code == 409


def test_missing_key_prevents_oauth(client, monkeypatch):
    monkeypatch.delenv('BERRY_ACCESS_KEY')
    assert client.post('/api/social/youtube/start', headers=headers(),
                       json={'channel_id': 'lab'}).status_code == 503


def test_tiktok_instagram_require_approved_https_redirect(client, monkeypatch):
    for p in ('tiktok', 'instagram'):
        monkeypatch.setenv(social_oauth.CLIENT_ID_ENV[p], 'demo-app-1234')
        secret = db.DB.parent / f'{p}-secret.txt'
        secret.write_text('private-secret')
        monkeypatch.setenv(social_oauth.SECRET_FILE_ENV[p], str(secret))
        r = client.post(f'/api/social/{p}/start', headers=headers(), json={'channel_id': 'lab'})
        assert r.status_code == 409
        assert 'HTTPS' in r.json()['detail']
    monkeypatch.setenv('BERRY_SOCIAL_REDIRECT_BASE', 'https://oauth.example.com')
    for p in ('tiktok', 'instagram'):
        result = client.post(f'/api/social/{p}/start', headers=headers(), json={'channel_id': 'lab'})
        assert result.status_code == 200, result.text
        assert result.json()['scope'] == social_oauth.SCOPE[p]
        assert 'video.publish' not in result.text
