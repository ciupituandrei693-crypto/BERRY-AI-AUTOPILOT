"""Integration tests for the local FastAPI backend. No network/external services."""
import pytest
from fastapi.testclient import TestClient
from berry import db
from berry.app import app

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db,'DB',tmp_path/'berry_test.sqlite3')
    with TestClient(app) as c:
        yield c

def test_seed_channels_and_characters(client):
    r=client.get('/api/channels')
    assert r.status_code==200
    assert len(r.json())==5
    characters=client.get('/api/characters').json()
    assert any(x['name']=='AFINA' and x['channel_id']=='lab' and 'Afină' in x['appearance'] for x in characters)
    assert any(x['name']=='AFINA STAR' and x['channel_id']=='beats' for x in characters)

def test_seo_templates_differ_by_channel(client):
    a=client.post('/api/seo/preview',json={'channel_id':'mind','content_type':'main90','topic':'influența în prietenie'})
    b=client.post('/api/seo/preview',json={'channel_id':'lab','content_type':'longform','topic':'se formează stelele'})
    assert a.status_code==200 and b.status_code==200
    assert '#FruitMind' in a.json()['hashtags']
    assert '#FruitLab' in b.json()['hashtags']
    assert a.json()['hook'] != b.json()['hook']
    assert b.json()['youtube']['format']=='Video lung 16:9'
    assert a.json()['status']=='DRAFT_TEMPLATE'

def add_item(client):
    r=client.post('/api/items',json={'channel_id':'wealth','content_type':'main90','topic':'economisirea pentru primul apartament'})
    assert r.status_code==201
    return r.json()['id']

def test_batch_approval_marks_not_published(client):
    id=add_item(client)
    b=client.post('/api/batches',json={'name':'Lot de test','item_ids':[id]})
    assert b.status_code==201
    b_id=b.json()['id']
    assert client.get('/api/items').json()[0]['status']=='IN_REVIEW'
    assert client.post(f'/api/batches/{b_id}/approve').json()=={'status':'APPROVED_NOT_PUBLISHED','published':False,'reason':'Nu există integrare API socială în această etapă.'}
    assert client.get('/api/items').json()[0]['status']=='APPROVED_NOT_PUBLISHED'
    assert client.post(f'/api/batches/{b_id}/approve').status_code==409
    assert client.delete(f'/api/items/{id}').status_code==409
    s=client.get('/api/status').json()
    assert s['real_publication_enabled'] is False and s['social_connections']==0

def test_reject_releases_draft(client):
    id=add_item(client)
    b_id=client.post('/api/batches',json={'name':'Lot de respins','item_ids':[id]}).json()['id']
    assert client.post(f'/api/batches/{b_id}/reject').json()['status']=='REJECTED'
    assert client.get('/api/items').json()[0]['status']=='DRAFT'

def test_budget_no_actual_spend(client):
    r=client.post('/api/spend-proposals',json={'category':'ADS','channel_id':'mind','amount':30,'note':'Test de promovare'})
    assert r.status_code==201 and r.json()['charged'] is False
    b=client.get('/api/budget').json()
    assert b['monthly_target_total']==750 and b['spend_executed_by_app']==0
    assert len(b['proposals'])==1 and b['proposals'][0]['status']=='PENDING'
    assert client.post('/api/spend-proposals',json={'category':'ADS','amount':22,'note':'Test fără canal'}).status_code==422

def test_kill_switch_active_by_default_and_log(client):
    assert client.get('/api/status').json()['kill_switch'] is True
    assert client.post('/api/settings/kill-switch',json={'enabled':False}).json()['outbound_publication_available'] is False
    assert client.get('/api/status').json()['kill_switch'] is False
    assert client.post('/api/settings/kill-switch',json={'enabled':True}).json()['kill_switch'] is True
    assert any(x['action']=='kill_switch' for x in client.get('/api/audit').json())

def test_invalid_items_and_duplicate_ids(client):
    id=add_item(client)
    assert client.post('/api/items',json={'channel_id':'unknown','content_type':'main90','topic':'example'}).status_code==422
    assert client.post('/api/batches',json={'name':'duplicate test','item_ids':[id,id]}).status_code==201
    assert client.post('/api/batches',json={'name':'same item again','item_ids':[id]}).status_code==409

def test_csv_export(client):
    add_item(client)
    res=client.get('/api/export.csv')
    assert res.status_code==200
    assert 'economisirea' in res.text
    assert 'text/csv' in res.headers['content-type']

def test_daily_plan_creates_25_drafts_once_and_weekday_only(client):
    r=client.post('/api/plan/day',json={'day':'2026-11-09'})
    assert r.status_code==201
    assert r.json()['items_created']==25 and r.json()['media_generated'] is False
    items=client.get('/api/items').json()
    assert len(items)==25
    assert sum(x['content_type']=='main90' for x in items)==5
    assert sum(x['content_type']=='short15' for x in items)==5
    assert sum(x['content_type']=='image' for x in items)==15
    assert all(x['status']=='DRAFT' for x in items)
    assert client.post('/api/plan/day',json={'day':'2026-11-09'}).status_code==409
    assert client.post('/api/plan/day',json={'day':'2026-11-08'}).status_code==422

def test_koboldcpp_does_not_allow_external_url(client,monkeypatch):
    from berry.local_ai import generate_text,LocalAIError
    monkeypatch.setenv('BERRY_KOBOLD_URL','https://example.org')
    with pytest.raises(LocalAIError):
        generate_text('mind','test subiect','main90')
