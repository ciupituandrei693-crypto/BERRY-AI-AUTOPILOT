"""User-controlled local social account linking routes. No upload or publishing."""
from __future__ import annotations

import hmac
import ipaddress
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Literal

from . import social_oauth

router = APIRouter(prefix='/api/social', tags=['Social OAuth — opt-in'])


def require_access(request: Request) -> None:
    key = os.getenv('BERRY_ACCESS_KEY', '')
    if len(key) < 16:
        raise HTTPException(503, 'Configureaza BERRY_ACCESS_KEY de minimum 16 caractere pentru OAuth')
    host = request.client.host if request.client else ''
    try:
        loopback = ipaddress.ip_address(host).is_loopback
    except ValueError:
        loopback = host == 'testclient'
    if not loopback:
        raise HTTPException(403, 'Conectarea sociala se administreaza doar local')
    if not hmac.compare_digest(request.headers.get('X-BERRY-KEY', ''), key):
        raise HTTPException(401, 'Cheie BERRY invalida')


class LinkRequest(BaseModel):
    channel_id: Literal['mind', 'wealth', 'beats', 'lab', 'heart']


@router.get('/status', dependencies=[Depends(require_access)])
def status():
    return social_oauth.status()


@router.post('/{provider}/start', dependencies=[Depends(require_access)])
def start(provider: Literal['youtube', 'tiktok', 'instagram'], data: LinkRequest):
    try:
        return social_oauth.start(provider, data.channel_id)
    except social_oauth.OAuthError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get('/{provider}/callback')
def callback(provider: Literal['youtube', 'tiktok', 'instagram'],
             state: str = '', code: str = '', error: str = ''):
    # The provider's browser redirect has no X-BERRY-KEY. The one-time random
    # state was issued only by an authenticated local POST and expires in 10 min.
    if error or not code or not state:
        return RedirectResponse('/?oauth=failed', status_code=303)
    try:
        social_oauth.callback(provider, state, code)
    except (social_oauth.OAuthError, ValueError):
        return RedirectResponse('/?oauth=failed', status_code=303)
    return RedirectResponse('/?oauth=connected', status_code=303)


@router.post('/youtube/channel-stats', dependencies=[Depends(require_access)])
def youtube_stats(data: LinkRequest):
    try:
        return social_oauth.youtube_channel_stats(data.channel_id)
    except social_oauth.OAuthError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post('/{provider}/disconnect', dependencies=[Depends(require_access)])
def disconnect(provider: Literal['youtube', 'tiktok', 'instagram'], data: LinkRequest):
    try:
        return social_oauth.disconnect(provider, data.channel_id)
    except social_oauth.OAuthError as exc:
        raise HTTPException(422, str(exc)) from exc
