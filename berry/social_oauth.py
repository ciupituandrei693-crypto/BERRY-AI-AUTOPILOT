"""Optional, explicit OAuth account linking for YouTube, TikTok and Instagram.

NO posting scopes, publishing, scheduled network tasks or cloud GPUs. OAuth is
disabled by default. Tokens are encrypted at rest with a local Fernet key.
TikTok and Instagram normally require a provider-approved HTTPS redirect URL;
BERRY never creates a public tunnel or server automatically.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from cryptography.fernet import Fernet
from . import db

PROVIDERS = ('youtube', 'tiktok', 'instagram')
SCOPE = {
    'youtube': 'https://www.googleapis.com/auth/youtube.readonly',
    'tiktok': 'user.info.basic',
    'instagram': 'instagram_business_basic',
}
CLIENT_ID_ENV = {
    'youtube': 'BERRY_GOOGLE_OAUTH_CLIENT_ID',
    'tiktok': 'BERRY_TIKTOK_CLIENT_KEY',
    'instagram': 'BERRY_INSTAGRAM_APP_ID',
}
SECRET_FILE_ENV = {
    'youtube': 'BERRY_GOOGLE_OAUTH_CLIENT_SECRET_FILE',
    'tiktok': 'BERRY_TIKTOK_CLIENT_SECRET_FILE',
    'instagram': 'BERRY_INSTAGRAM_APP_SECRET_FILE',
}
AUTH_URL = {
    'youtube': 'https://accounts.google.com/o/oauth2/v2/auth',
    'tiktok': 'https://www.tiktok.com/v2/auth/authorize/',
    'instagram': 'https://www.instagram.com/oauth/authorize',
}
TOKEN_URL = {
    'youtube': 'https://oauth2.googleapis.com/token',
    'tiktok': 'https://open.tiktokapis.com/v2/oauth/token/',
    'instagram': 'https://api.instagram.com/oauth/access_token',
}
CHANNEL_IDS = {c[0] for c in db.CHANNELS}


class OAuthError(ValueError):
    pass


def enabled() -> bool:
    return os.getenv('BERRY_SOCIAL_OAUTH_ENABLED', '').strip().lower() == 'true'


def _secret(provider: str) -> str:
    file = os.getenv(SECRET_FILE_ENV[provider], '')
    if not file:
        raise OAuthError('Lipseste fisierul privat de client secret')
    path = Path(file).expanduser()
    if not path.is_file() or path.stat().st_size > 8192:
        raise OAuthError('Fisierul privat client secret nu exista sau este prea mare')
    raw = path.read_text(encoding='utf-8-sig').strip()
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            obj = obj.get('web', obj)
            raw = str(obj.get('client_secret', '') or obj.get('app_secret', '')).strip()
    except json.JSONDecodeError:
        pass
    if not raw or len(raw) > 1024:
        raise OAuthError('Client secret invalid')
    return raw


def _redirect(provider: str) -> str:
    base = os.getenv('BERRY_SOCIAL_REDIRECT_BASE', 'http://localhost:8765').strip().rstrip('/')
    parts = urllib.parse.urlsplit(base)
    if parts.username or parts.password or parts.query or parts.fragment or parts.path not in ('', '/'):
        raise OAuthError('Baza redirect OAuth trebuie sa fie doar origine, fara path/query')
    if provider == 'youtube':
        if base != 'http://localhost:8765':
            raise OAuthError('YouTube OAuth local accepta doar http://localhost:8765')
    else:
        if parts.scheme != 'https' or not parts.hostname:
            raise OAuthError('TikTok si Instagram necesita un redirect HTTPS aprobat de platforma')
        if parts.hostname in ('localhost', '127.0.0.1'):
            raise OAuthError('Pentru TikTok/Instagram configureaza un host HTTPS public aprobat')
    return base + f'/api/social/{provider}/callback'


def _client_id(provider: str) -> str:
    value = os.getenv(CLIENT_ID_ENV[provider], '').strip()
    if not re.fullmatch(r'[A-Za-z0-9_.-]{4,300}', value):
        raise OAuthError('Client ID / client key invalid sau lipsa')
    if provider == 'youtube' and not value.endswith('.apps.googleusercontent.com'):
        raise OAuthError('Google OAuth client ID invalid')
    return value


def _key_path() -> Path:
    base = Path(os.getenv('LOCALAPPDATA') or str(Path.home() / '.berry_ai_autopilot'))
    return base / 'BERRY_AI_AUTOPILOT' / 'private' / 'social_fernet.key'


def _fernet() -> Fernet:
    path = _key_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        # Exclusive create; the key is never committed or placed in the project.
        try:
            with path.open('xb') as file:
                file.write(Fernet.generate_key())
            if os.name != 'nt':
                path.chmod(0o600)
        except FileExistsError:
            pass
    return Fernet(path.read_bytes())


def _encrypt(obj: dict) -> str:
    return _fernet().encrypt(json.dumps(obj, ensure_ascii=False).encode()).decode('ascii')


def _pkce() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    return verifier, challenge


def init() -> None:
    with db.connection() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS social_oauth_flows(
          state_hash TEXT PRIMARY KEY,
          provider TEXT NOT NULL,
          channel_id TEXT NOT NULL,
          verifier_cipher TEXT NOT NULL,
          redirect_uri TEXT NOT NULL,
          expires_unix INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS social_accounts(
          provider TEXT NOT NULL,
          channel_id TEXT NOT NULL,
          account_id TEXT NOT NULL,
          display_name TEXT NOT NULL,
          scopes TEXT NOT NULL,
          token_cipher TEXT NOT NULL,
          connected_at TEXT NOT NULL,
          PRIMARY KEY(provider,channel_id));
        ''')


def status() -> dict:
    rows = db.all_rows('SELECT provider,channel_id,account_id,display_name,scopes,connected_at FROM social_accounts')
    return {
        'enabled': enabled(), 'publishing_enabled': False, 'upload_scopes_requested': False,
        'requires_explicit_account_authorization': True,
        'providers': {
            p: {
                'configured': bool(os.getenv(CLIENT_ID_ENV[p]) and os.getenv(SECRET_FILE_ENV[p])),
                'redirect_ready': _redirect_ready(p),
                'scope': SCOPE[p],
                'connected': [dict(x) for x in rows if x['provider'] == p],
                'publishing_enabled': False,
            } for p in PROVIDERS
        },
    }


def _redirect_ready(provider: str) -> bool:
    try:
        _redirect(provider)
        return True
    except OAuthError:
        return False


def start(provider: str, channel_id: str) -> dict:
    if provider not in PROVIDERS or channel_id not in CHANNEL_IDS:
        raise OAuthError('Platforma sau canal invalid')
    if not enabled():
        raise OAuthError('OAuth este dezactivat; activeaza-l explicit dupa configurare')
    client = _client_id(provider)
    _secret(provider)  # fail early, without returning the secret
    redirect = _redirect(provider)
    verifier, challenge = _pkce()
    state = secrets.token_urlsafe(48)
    params = {
        'response_type': 'code',
        'redirect_uri': redirect,
        'scope': SCOPE[provider],
        'state': state,
    }
    if provider == 'youtube':
        params.update({'client_id': client, 'access_type': 'offline',
                       'prompt': 'select_account consent',
                       'code_challenge': challenge, 'code_challenge_method': 'S256'})
    elif provider == 'tiktok':
        params.update({'client_key': client, 'code_challenge': challenge,
                       'code_challenge_method': 'S256'})
    else:
        params.update({'client_id': client, 'enable_fb_login': '0',
                       'force_authentication': '1'})
    with db.connection() as con:
        con.execute('DELETE FROM social_oauth_flows WHERE expires_unix<?', (int(time.time()),))
        con.execute('''INSERT INTO social_oauth_flows
            (state_hash,provider,channel_id,verifier_cipher,redirect_uri,expires_unix)
            VALUES(?,?,?,?,?,?)''',
            (hashlib.sha256(state.encode()).hexdigest(), provider, channel_id,
             _encrypt({'verifier': verifier}), redirect, int(time.time()) + 600))
        db.audit(con, 'social_oauth_started', {'provider': provider, 'channel_id': channel_id})
    return {'provider': provider, 'channel_id': channel_id,
            'authorization_url': AUTH_URL[provider] + '?' + urllib.parse.urlencode(params),
            'scope': SCOPE[provider], 'expires_in_seconds': 600,
            'publishing_enabled': False}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise OAuthError('Redirect HTTP neasteptat la OAuth')


OPENER = urllib.request.build_opener(NoRedirect())


def _json_request(url: str, *, data: dict | None = None, bearer: str = '') -> dict:
    # Only hard-coded provider URLs are passed by callers, never user-provided.
    payload = urllib.parse.urlencode(data).encode() if data is not None else None
    headers = {'Accept': 'application/json', 'User-Agent': 'BERRY-AI-AUTOPILOT/1'}
    if data is not None:
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
    if bearer:
        headers['Authorization'] = 'Bearer ' + bearer
    request = urllib.request.Request(url, data=payload, headers=headers,
                                     method='POST' if data is not None else 'GET')
    try:
        with OPENER.open(request, timeout=15) as response:
            if int(response.headers.get('Content-Length') or 0) > 100_000:
                raise OAuthError('Raspuns OAuth prea mare')
            raw = response.read(100_001)
            if len(raw) > 100_000:
                raise OAuthError('Raspuns OAuth prea mare')
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise OAuthError('Raspuns OAuth invalid')
            return result
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
            json.JSONDecodeError) as exc:
        # Never expose provider errors that could contain authorization codes.
        raise OAuthError('Schimbul OAuth sau verificarea contului a esuat') from exc


def _exchange(provider: str, code: str, redirect: str, verifier: str) -> tuple[dict, str, str]:
    params = {
        'client_id': _client_id(provider),
        'client_secret': _secret(provider),
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect,
    }
    if provider in ('youtube', 'tiktok'):
        params['code_verifier'] = verifier
    if provider == 'tiktok':
        params['client_key'] = params.pop('client_id')
    token = _json_request(TOKEN_URL[provider], data=params)
    access = token.get('access_token')
    if not isinstance(access, str) or not access:
        raise OAuthError('Platforma nu a returnat access_token')
    if provider == 'youtube':
        payload = _json_request('https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true',
                                bearer=access)
        channels = payload.get('items') or []
        if not channels:
            raise OAuthError('Contul Google nu are un canal YouTube verificabil')
        first = channels[0]
        account_id = str(first.get('id', ''))
        display = str(first.get('snippet', {}).get('title', ''))[:100]
        if not re.fullmatch(r'UC[A-Za-z0-9_-]{22}', account_id):
            raise OAuthError('Canal YouTube invalid')
    elif provider == 'tiktok':
        payload = _json_request('https://open.tiktokapis.com/v2/user/info/?fields=open_id,display_name',
                                bearer=access)
        user = (payload.get('data') or {}).get('user') or {}
        account_id = str(user.get('open_id') or token.get('open_id') or '')
        display = str(user.get('display_name') or account_id)[:100]
        if not account_id:
            raise OAuthError('TikTok nu a confirmat identitatea')
    else:
        # Instagram API with Instagram Login, business-basic read scope.
        url = 'https://graph.instagram.com/me?' + urllib.parse.urlencode(
            {'fields': 'id,username,account_type', 'access_token': access})
        user = _json_request(url)
        account_id = str(user.get('id') or token.get('user_id') or '')
        display = str(user.get('username') or account_id)[:100]
        if not account_id:
            raise OAuthError('Instagram nu a confirmat identitatea')
    return token, account_id, display


def callback(provider: str, state: str, code: str) -> dict:
    if provider not in PROVIDERS or not enabled():
        raise OAuthError('OAuth dezactivat')
    if not re.fullmatch(r'[A-Za-z0-9_-]{32,256}', state) or not (4 <= len(code) <= 4096):
        raise OAuthError('State sau cod OAuth invalid')
    digest = hashlib.sha256(state.encode()).hexdigest()
    with db.connection() as con:
        flow = con.execute('SELECT * FROM social_oauth_flows WHERE state_hash=?', (digest,)).fetchone()
        if not flow:
            raise OAuthError('State OAuth necunoscut sau deja utilizat')
        # Consume one-time state before any external request, even if exchange fails.
        con.execute('DELETE FROM social_oauth_flows WHERE state_hash=?', (digest,))
        if flow['provider'] != provider or flow['expires_unix'] < int(time.time()):
            raise OAuthError('State OAuth expirat sau platforma diferita')
    verifier = json.loads(_fernet().decrypt(flow['verifier_cipher'].encode()))['verifier']
    token, account_id, display = _exchange(provider, code, flow['redirect_uri'], verifier)
    with db.connection() as con:
        con.execute('''INSERT INTO social_accounts
            (provider,channel_id,account_id,display_name,scopes,token_cipher,connected_at)
            VALUES(?,?,?,?,?,?,?) ON CONFLICT(provider,channel_id) DO UPDATE SET
            account_id=excluded.account_id,display_name=excluded.display_name,
            scopes=excluded.scopes,token_cipher=excluded.token_cipher,
            connected_at=excluded.connected_at''',
            (provider, flow['channel_id'], account_id, display, SCOPE[provider],
             _encrypt(token), db.utcnow()))
        db.audit(con, 'social_oauth_connected',
                 {'provider': provider, 'channel_id': flow['channel_id']})
    return {'provider': provider, 'channel_id': flow['channel_id'],
            'account_id': account_id, 'display_name': display,
            'publishing_enabled': False}


def disconnect(provider: str, channel_id: str) -> dict:
    if provider not in PROVIDERS or channel_id not in CHANNEL_IDS:
        raise OAuthError('Platforma sau canal invalid')
    with db.connection() as con:
        cur = con.execute('DELETE FROM social_accounts WHERE provider=? AND channel_id=?',
                          (provider, channel_id))
        db.audit(con, 'social_oauth_local_disconnected',
                 {'provider': provider, 'channel_id': channel_id})
    return {'disconnected_locally': bool(cur.rowcount), 'remote_token_revoked': False,
            'note': 'Revoca separat accesul si din setarile contului platformei'}
