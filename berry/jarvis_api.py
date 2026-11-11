"""Local, authenticated JARVIS ONE ULTIMATE control API for BERRY.

JARVIS can create and render local drafts and inspect their QA. It CANNOT approve
on behalf of a human, publish to social platforms, spend, or start cloud services.
No separate BERRY chatbot or avatar is created.
"""
from __future__ import annotations

import hmac
import ipaddress
import json
import os
import re
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Literal

from . import db, engines, seo, studio, workflow

router = APIRouter(prefix='/api/v1/jarvis', tags=['JARVIS ONE LOCAL'])


def guard(request: Request) -> None:
    """Separate secret and loopback-only caller; never silently disable auth."""
    key = os.getenv('BERRY_JARVIS_API_KEY', '')
    if len(key) < 32:
        raise HTTPException(503, 'API JARVIS neconfigurat: cheia separata trebuie sa aiba minimum 32 caractere')
    host = request.client.host if request.client else ''
    try:
        loopback = ipaddress.ip_address(host).is_loopback
    except ValueError:
        loopback = host == 'testclient'  # Starlette in-process test client
    if not loopback:
        raise HTTPException(403, 'JARVIS API permite doar apeluri locale')
    if not hmac.compare_digest(request.headers.get('X-JARVIS-KEY', ''), key):
        raise HTTPException(401, 'Cheie JARVIS invalida')


secured = [Depends(guard)]


def init() -> None:
    with db.connection() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS jarvis_packages(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          request_id TEXT NOT NULL UNIQUE,
          item_id INTEGER NOT NULL UNIQUE REFERENCES items(id),
          status TEXT NOT NULL DEFAULT 'DRAFT',
          render_job_id INTEGER,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS jarvis_events(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          package_id INTEGER NOT NULL REFERENCES jarvis_packages(id),
          kind TEXT NOT NULL,
          details_json TEXT NOT NULL,
          created_at TEXT NOT NULL);
        ''')


def event(con, package_id: int, kind: str, details: dict | None = None) -> None:
    con.execute('INSERT INTO jarvis_events(package_id,kind,details_json,created_at) VALUES(?,?,?,?)',
                (package_id, kind, json.dumps(details or {}, ensure_ascii=False), db.utcnow()))


class NewPackage(BaseModel):
    request_id: str = Field(min_length=8, max_length=100, pattern=r'^[A-Za-z0-9_.-]+$')
    channel_id: Literal['mind', 'wealth', 'beats', 'lab', 'heart']
    content_type: Literal['main90', 'short15', 'image', 'longform']
    topic: str = Field(min_length=3, max_length=300)
    title: str = Field(default='', max_length=200)


def row(package_id: int) -> dict:
    p = db.one_row('''SELECT p.*, i.channel_id,i.content_type,i.topic,i.title,i.status AS item_status
                      FROM jarvis_packages p JOIN items i ON i.id=p.item_id WHERE p.id=?''',
                   (package_id,))
    if not p:
        raise HTTPException(404, 'Pachet JARVIS inexistent')
    if p['render_job_id']:
        job = studio.get_job(p['render_job_id'])
        p['render'] = {'job_id': job['id'], 'status': job['status'],
                       'result': job['result'], 'error': job['error']} if job else None
    else:
        p['render'] = None
    p['external_cost_usd'] = 0
    p['published'] = False
    return p


@router.get('/capabilities', dependencies=secured)
def capabilities():
    return {
        'department': 'BERRY_AI_AUTOPILOT', 'assistant': 'JARVIS_ONE_ULTIMATE',
        'channels': [c[0] for c in db.CHANNELS],
        'local_render': studio.capabilities(),
        'local_engines': engines.status(),
        'package_creation': True, 'local_render_submission': True,
        'quality_checks': True, 'human_review_required': True,
        'human_approval_via_berry_dashboard_only': True,
        'social_login': False, 'social_publishing': False,
        'cloud_gpu': False, 'external_server': False, 'external_spend_usd': 0,
    }


@router.post('/packages', status_code=201, dependencies=secured)
def create_package(data: NewPackage):
    with db.connection() as con:
        existing = con.execute('''SELECT p.id,i.channel_id,i.content_type,i.topic,i.title
                                  FROM jarvis_packages p JOIN items i ON i.id=p.item_id
                                  WHERE p.request_id=?''', (data.request_id,)).fetchone()
        title = data.title.strip() or seo.draft(data.channel_id, data.topic, data.content_type)['title']
        if existing:
            same = (existing['channel_id'], existing['content_type'], existing['topic'], existing['title']) == (
                data.channel_id, data.content_type, data.topic, title)
            if not same:
                raise HTTPException(409, 'request_id exista deja pentru un continut diferit')
            package_id = existing['id']
        else:
            now = db.utcnow()
            draft = seo.draft(data.channel_id, data.topic, data.content_type)
            item = con.execute('''INSERT INTO items(channel_id,content_type,topic,title,seo_json,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?)''', (data.channel_id, data.content_type, data.topic, title,
                                          json.dumps(draft, ensure_ascii=False), now, now))
            cur = con.execute('''INSERT INTO jarvis_packages(request_id,item_id,created_at,updated_at)
                VALUES(?,?,?,?)''', (data.request_id, item.lastrowid, now, now))
            package_id = cur.lastrowid
            event(con, package_id, 'DRAFT_CREATED', {'item_id': item.lastrowid})
            db.audit(con, 'jarvis_local_draft_created', {'package_id': package_id})
    return row(package_id)


@router.get('/packages', dependencies=secured)
def list_packages():
    return [row(p['id']) for p in db.all_rows(
        'SELECT id FROM jarvis_packages ORDER BY id DESC LIMIT 100')]


@router.get('/packages/{package_id}', dependencies=secured)
def get_package(package_id: int):
    return row(package_id)


@router.get('/packages/{package_id}/events', dependencies=secured)
def get_events(package_id: int):
    row(package_id)
    events = db.all_rows('''SELECT id,kind,details_json,created_at FROM jarvis_events
                            WHERE package_id=? ORDER BY id ASC''', (package_id,))
    for e in events:
        e['details'] = json.loads(e.pop('details_json'))
    return events


@router.post('/packages/{package_id}/render-local', status_code=202, dependencies=secured)
def render_local(package_id: int):
    p = row(package_id)
    if p['render'] and p['render']['status'] in ('QUEUED', 'RUNNING', 'DONE'):
        raise HTTPException(409, 'Randarea exista deja; consulta starea')
    if p['item_status'] != 'DRAFT':
        raise HTTPException(409, 'Randarea este permisa doar pentru DRAFT')
    try:
        job_id = studio.submit(p['item_id'], 'full')
    except (ValueError, LookupError) as exc:
        raise HTTPException(409, str(exc)) from exc
    with db.connection() as con:
        con.execute('UPDATE jarvis_packages SET render_job_id=?,status=?,updated_at=? WHERE id=?',
                    (job_id, 'RENDER_SUBMITTED', db.utcnow(), package_id))
        event(con, package_id, 'LOCAL_RENDER_SUBMITTED', {'job_id': job_id})
    return {'package_id': package_id, 'job_id': job_id, 'status': 'QUEUED',
            'local_only': True, 'external_cost_usd': 0}


@router.get('/packages/{package_id}/qa', dependencies=secured)
def quality(package_id: int):
    p = row(package_id)
    try:
        return workflow.quality(p['item_id'])
    except (ValueError, LookupError) as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post('/packages/{package_id}/review-request', dependencies=secured)
def review_request(package_id: int):
    p = row(package_id)
    if p['item_status'] != 'DRAFT':
        raise HTTPException(409, 'Materialul nu mai este DRAFT')
    with db.connection() as con:
        con.execute('UPDATE jarvis_packages SET status=?,updated_at=? WHERE id=?',
                    ('REVIEW_REQUESTED', db.utcnow(), package_id))
        event(con, package_id, 'HUMAN_REVIEW_REQUESTED',
              {'note': 'Aprobarea se face doar din BERRY dashboard'})
    return {'status': 'REVIEW_REQUESTED', 'approved': False, 'published': False}


@router.post('/packages/{package_id}/approve', dependencies=secured)
def approve_locked(package_id: int):
    row(package_id)
    raise HTTPException(423, 'JARVIS nu poate aproba in numele utilizatorului')


@router.post('/packages/{package_id}/publish', dependencies=secured)
def publish_locked(package_id: int):
    row(package_id)
    raise HTTPException(423, 'Publicarea externa este dezactivata si necesita aprobare separata')


@router.post('/cloud/activate', dependencies=secured)
def cloud_locked():
    raise HTTPException(423, 'GPU cloud si serverul extern nu pot fi activate prin JARVIS API')
