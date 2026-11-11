"""YouTube OAuth preparation tests. All tests are offline, with no Google calls."""
from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from berry import db, youtube_oauth
from berry import app as app_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'DB', tmp_path / 'berry_test.sqlite3')
    monkeypatch.setattr(app_module, 'KEY', '')
    monkeypatch.delenv('BERRY_GOOGLE_OAUTH_CLIENT_ID', raising=False)
    monkeypatch.delenv('BERRY_GOOGLE_OAUTH_CLIENT_SECRET_FILE', raising=False)
    with TestClient(app_module.app) as c:
        yield c


def test_offline_plan_has_five_unconnected_brands(client, monkeypatch):
    def block(*args, **kwargs):
        raise AssertionError('No network calls allowed')
    monkeypatch.setattr('urllib.request.urlopen', block)
    r = client.get('/api/integrations/youtube/plan')
    assert r.status_code == 200
    data = r.json()
    assert data['mode'] == 'PREPARED_OFFLINE'
    assert data['live_oauth_enabled'] is False
    assert data['connected_count'] == 0
    assert data['planned_count'] == 0
    assert data['requested_scopes'] == [youtube_oauth.YOUTUBE_READONLY_SCOPE]
    assert data['upload_scope_requested'] is False
    assert data['publishing_enabled'] is False
    assert len(data['channels']) == 5
    assert all(not c['connected'] and not c['can_publish'] for c in data['channels'])
    assert 'access_token' not in str(data)


def test_offline_local_channel_planning_and_unique_ids(client):
    yt_id = 'UC' + 'A' * 22
    r = client.post('/api/integrations/youtube/channel-plan', json={
        'fruit_channel_id': 'lab', 'youtube_channel_id': yt_id, 'display_label': 'Fruit Lab'})
    assert r.status_code == 201
    assert r.json()['connected'] is False
    status = client.get('/api/integrations/youtube/plan').json()
    lab = next(x for x in status['channels'] if x['fruit_channel_id'] == 'lab')
    assert lab['youtube_channel_id'] == yt_id
    assert lab['verified'] is False
    assert status['connected_count'] == 0
    assert status['planned_count'] == 1
    assert client.post('/api/integrations/youtube/channel-plan', json={
        'fruit_channel_id': 'beats', 'youtube_channel_id': yt_id}).status_code == 409
    assert client.post('/api/integrations/youtube/channel-plan', json={
        'fruit_channel_id': 'heart', 'youtube_channel_id': 'invalid'}).status_code == 422
    assert client.post('/api/integrations/youtube/channel-plan', json={
        'fruit_channel_id': 'unknown'}).status_code == 422
    assert client.delete('/api/integrations/youtube/channel-plan/lab').json()['deleted'] is True
    assert client.get('/api/integrations/youtube/plan').json()['planned_count'] == 0
    assert any(x['action'] == 'youtube_channel_plan_local_only' for x in client.get('/api/audit').json())


def test_authorization_callback_and_upload_are_locked(client):
    assert client.get('/api/integrations/youtube/connect').status_code == 423
    assert client.get('/api/integrations/youtube/callback?code=should-not-be-used&state=bad').status_code == 423
    assert client.post('/api/integrations/youtube/upload', json={}).status_code == 423
    status = client.get('/api/status').json()
    assert status['social_connections'] == 0
    assert status['real_publication_enabled'] is False


def test_pkce_and_consent_url_are_pure_and_readonly():
    verifier, challenge = youtube_oauth.new_pkce()
    assert len(verifier) >= 43 and len(challenge) == 43
    url = youtube_oauth.authorization_url('demo.apps.googleusercontent.com', 'A' * 48, challenge)
    parts = urlparse(url)
    q = parse_qs(parts.query)
    assert parts.hostname == 'accounts.google.com'
    assert q['scope'] == [youtube_oauth.YOUTUBE_READONLY_SCOPE]
    assert q['code_challenge_method'] == ['S256']
    assert q['redirect_uri'] == [youtube_oauth.LOCAL_REDIRECT_URI]
    assert 'youtube.upload' not in url
    with pytest.raises(ValueError):
        youtube_oauth.authorization_url('demo.apps.googleusercontent.com', 'A' * 48, challenge,
                                        redirect_uri='https://evil.example/callback')
    with pytest.raises(ValueError):
        youtube_oauth.authorization_url('demo.apps.googleusercontent.com', 'short', challenge)


def test_local_security_origin_and_access_key(client, monkeypatch):
    r = client.post('/api/integrations/youtube/channel-plan', headers={'Origin': 'https://evil.example'},
                    json={'fruit_channel_id': 'lab'})
    assert r.status_code == 403
    monkeypatch.setattr(app_module, 'KEY', 'local-secret')
    assert client.get('/api/integrations/youtube/plan').status_code == 401
    assert client.get('/api/integrations/youtube/plan', headers={'X-BERRY-KEY': 'local-secret'}).status_code == 200


def test_staged_credentials_never_returned(client, monkeypatch, tmp_path):
    secret = tmp_path / 'private-client.json'
    secret.write_text('{"client_secret":"PRIVATE_VALUE"}')
    monkeypatch.setenv('BERRY_GOOGLE_OAUTH_CLIENT_ID', 'example.apps.googleusercontent.com')
    monkeypatch.setenv('BERRY_GOOGLE_OAUTH_CLIENT_SECRET_FILE', str(secret))
    r = client.get('/api/integrations/youtube/plan')
    assert r.status_code == 200
    assert r.json()['client_id_staged'] is True
    assert r.json()['client_secret_file_staged'] is True
    assert 'PRIVATE_VALUE' not in r.text
    assert str(secret) not in r.text


def test_channel_parser_ignores_invalid_response():
    result = youtube_oauth.parse_my_channel_response({'items': [
        {'id': 'UC' + 'B' * 22, 'snippet': {'title': 'Fruit Science'}},
        {'id': 'invalid'},
    ]})
    assert len(result) == 1
    assert result[0]['title'] == 'Fruit Science'
    assert result[0]['verified_by_google'] is False
