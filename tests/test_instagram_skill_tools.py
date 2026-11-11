"""Offline contract tests for the 3 SHA256-pinned Instagram content tools."""
import hashlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from berry import db, instagram_skill_tools as ig
from berry import app as app_module


@pytest.fixture
def fake_source(tmp_path, monkeypatch):
    root = tmp_path / 'InstagramAgentSkill'
    script = root / 'skills' / 'ig-reel' / 'hookscore.py'
    script.parent.mkdir(parents=True)
    script.write_text('import json,sys\n'
                      'text=sys.stdin.read()\n'
                      'print(json.dumps({"hook":text,"score":70}))\n', encoding='utf8')
    digest = hashlib.sha256(script.read_bytes()).hexdigest()
    monkeypatch.setenv('BERRY_INSTAGRAM_SKILL_ROOT', str(root))
    monkeypatch.setattr(ig, 'SCRIPTS', {'hook': ('skills/ig-reel/hookscore.py', digest)})
    return root, script


def test_source_integrity_enforced(fake_source):
    root, script = fake_source
    assert ig.checked_script('hook') == script.resolve()
    script.write_text('print("tampered")\n', encoding='utf8')
    with pytest.raises(ig.InstagramToolError, match='modificat'):
        ig.checked_script('hook')


def test_offline_hook_analysis(fake_source):
    result = ig.analyze('hook', '3 greșeli frecvente')
    assert result['result']['score'] == 70
    assert result['offline'] is True
    assert result['published'] is False
    assert result['account_connected'] is False


def test_invalid_inputs_and_missing_scripts(fake_source):
    with pytest.raises(ig.InstagramToolError):
        ig.analyze('hook', 'x' * 241)
    with pytest.raises(ig.InstagramToolError):
        ig.analyze('beats', 'hello')
    with pytest.raises(ig.InstagramToolError):
        ig.analyze('hook', '')
    with pytest.raises(ig.InstagramToolError):
        ig.analyze('hook', 'hello', target=601)


def test_guarded_api_returns_offline_analysis(fake_source, tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'DB', tmp_path / 'berry.sqlite3')
    monkeypatch.setattr(app_module, 'KEY', '')
    with TestClient(app_module.app) as client:
        r = client.post('/api/seo/instagram/analyze',
                        json={'kind': 'hook', 'text': '3 greșeli frecvente'})
        assert r.status_code == 200
        assert r.json()['offline'] is True
        assert r.json()['published'] is False
        bad = client.post('/api/seo/instagram/analyze',
                          json={'kind': 'hook', 'text': 'x' * 241})
        assert bad.status_code == 422
        blocked = client.post('/api/seo/instagram/analyze',
                              headers={'Origin': 'https://attacker.example'},
                              json={'kind': 'hook', 'text': '3 greșeli'})
        assert blocked.status_code == 403
