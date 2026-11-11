"""Offline YouTube OAuth blueprint. NO live OAuth, token exchange, or uploads.

The helpers here are pure: building a URL does not send requests. The BERRY
application deliberately does not expose an authorization/start endpoint.
"""
from __future__ import annotations

import base64
import hashlib
import os
import re
import secrets
from pathlib import Path
from urllib.parse import urlencode

YOUTUBE_READONLY_SCOPE = 'https://www.googleapis.com/auth/youtube.readonly'
YOUTUBE_UPLOAD_SCOPE = 'https://www.googleapis.com/auth/youtube.upload'  # NOT REQUESTED
GOOGLE_AUTHORIZATION_ENDPOINT = 'https://accounts.google.com/o/oauth2/v2/auth'
LOCAL_REDIRECT_URI = 'http://localhost:8765/api/integrations/youtube/callback'
CHANNEL_ID_PATTERN = re.compile(r'^UC[A-Za-z0-9_-]{22}$')


def new_pkce() -> tuple[str, str]:
    """Return PKCE verifier/challenge for a future, approved OAuth flow."""
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode('ascii')).digest()).rstrip(b'=').decode('ascii')
    return verifier, challenge


def authorization_url(client_id: str, state: str, challenge: str,
                      redirect_uri: str = LOCAL_REDIRECT_URI) -> str:
    """Generate (not open) a read-only Google consent URL for offline unit tests.

    A future approved implementation must store one-time state, PKCE verifier
    and originating BERRY session securely, expire them, and verify on callback.
    """
    if not client_id or len(client_id) > 300 or not client_id.endswith('.apps.googleusercontent.com'):
        raise ValueError('Client ID Google invalid')
    if not re.fullmatch(r'[A-Za-z0-9_-]{32,256}', state):
        raise ValueError('State OAuth invalid')
    if not re.fullmatch(r'[A-Za-z0-9_-]{43}', challenge):
        raise ValueError('PKCE challenge invalid')
    if redirect_uri != LOCAL_REDIRECT_URI:
        raise ValueError('Redirect URI trebuie sa fie exact URI-ul local aprobat')
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': YOUTUBE_READONLY_SCOPE,
        'state': state,
        'code_challenge': challenge,
        'code_challenge_method': 'S256',
        'access_type': 'offline',
        'prompt': 'select_account',
    }
    return GOOGLE_AUTHORIZATION_ENDPOINT + '?' + urlencode(params)


def parse_my_channel_response(payload: dict) -> list[dict]:
    """Parse a *provided* channels.list(mine=true) response, without any API call."""
    if not isinstance(payload, dict):
        raise ValueError('Raspuns YouTube invalid')
    result = []
    for item in payload.get('items', []):
        if not isinstance(item, dict):
            continue
        channel_id = item.get('id', '')
        if not isinstance(channel_id, str) or not CHANNEL_ID_PATTERN.fullmatch(channel_id):
            continue
        snippet = item.get('snippet', {})
        if not isinstance(snippet, dict):
            snippet = {}
        title = snippet.get('title', '')
        result.append({'youtube_channel_id': channel_id,
                       'title': str(title)[:100],
                       'verified_by_google': False})  # offline parser cannot verify identity
    return result


def configuration_flags() -> dict:
    """Only report whether optional credentials are staged; never read or return them."""
    client_id = os.getenv('BERRY_GOOGLE_OAUTH_CLIENT_ID', '').strip()
    secret_file = os.getenv('BERRY_GOOGLE_OAUTH_CLIENT_SECRET_FILE', '').strip()
    # Only check presence; never parse, log, or upload secrets.
    secret_present = bool(secret_file and Path(secret_file).is_file())
    return {'client_id_staged': bool(client_id), 'client_secret_file_staged': secret_present}


def blueprint() -> dict:
    return {
        'provider': 'google_youtube',
        'mode': 'PREPARED_OFFLINE',
        'live_oauth_enabled': False,
        'connected_count': 0,
        'publishing_enabled': False,
        'upload_scope_requested': False,
        'requested_scopes': [YOUTUBE_READONLY_SCOPE],
        'future_upload_scope': YOUTUBE_UPLOAD_SCOPE,
        'redirect_uri_for_future_windows_test': LOCAL_REDIRECT_URI,
        'authorization_method': 'OAuth 2.0 authorization code + PKCE S256 + CSRF state',
        'channel_discovery_after_approval': 'GET https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true',
        'google_cloud_setup': 'YouTube Data API v3 + OAuth consent screen + Web application OAuth client',
        'no_token_storage': True,
        'no_network_requests': True,
        **configuration_flags(),
    }
