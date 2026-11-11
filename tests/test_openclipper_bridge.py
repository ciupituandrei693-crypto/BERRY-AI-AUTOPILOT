"""OpenClipper MCP bridge tests: mock local server, never touch network."""
import json

import pytest
from fastapi.testclient import TestClient

from berry import db, openclipper_bridge as oc
from berry.app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'DB', tmp_path / 'berry.sqlite3')
    with TestClient(app) as c:
        yield c


def test_reject_mutating_mcp_tools(monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError('No network should be attempted')
    monkeypatch.setattr(oc, '_call', no_network)
    with pytest.raises(oc.OpenClipperError):
        oc.list_local('patch_ai_clips')
    with pytest.raises(oc.OpenClipperError):
        oc.list_local('patch_export_social_metadata')


def test_mocked_read_only_list(client, monkeypatch):
    calls = []
    def fake_call(message, *, session=''):
        calls.append(message['method'])
        if message['method'] == 'initialize':
            return {'jsonrpc': '2.0', 'id': 1, 'result': {}}, 'local-session'
        if message['method'] == 'notifications/initialized':
            return {}, session
        assert message['params']['name'] == 'list_projects'
        return {'jsonrpc': '2.0', 'id': 2,
                'result': {'content': [{'type': 'text',
                                       'text': json.dumps({'items': [{'projectId': 'p1'}], 'total': 1})}]}}, session
    monkeypatch.setattr(oc, '_call', fake_call)
    r = client.get('/api/openclipper/list_projects')
    assert r.status_code == 200
    assert r.json()['data']['total'] == 1
    assert r.json()['read_only'] is True
    assert r.json()['published'] is False
    assert calls == ['initialize', 'notifications/initialized', 'tools/call']


def test_port_is_loopback_only(monkeypatch):
    monkeypatch.setenv('OPEN_CLIPPER_MCP_PORT', '12742')
    assert oc._endpoint() == 'http://127.0.0.1:12742/mcp'
    monkeypatch.setenv('OPEN_CLIPPER_MCP_PORT', '99999')
    with pytest.raises(oc.OpenClipperError):
        oc._endpoint()
