"""Read-only local OpenClipper MCP bridge (Streamable HTTP / JSON-RPC).

Only list_projects and list_exports. No clip modifications, publishing,
remote URL, credential transfer or shell. OpenClipper desktop must be running.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request


class OpenClipperError(ValueError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise OpenClipperError('Redirect interzis in MCP local')


OPENER = urllib.request.build_opener(NoRedirect())
ALLOWED_TOOLS = {'list_projects', 'list_exports'}


def _port() -> int:
    value = os.getenv('OPEN_CLIPPER_MCP_PORT', '12742')
    try:
        port = int(value)
    except ValueError as exc:
        raise OpenClipperError('Port MCP invalid') from exc
    if not 1024 <= port <= 65535:
        raise OpenClipperError('Port MCP in afara intervalului')
    return port


def _endpoint() -> str:
    return f'http://127.0.0.1:{_port()}/mcp'


def _call(message: dict, *, session: str = '') -> tuple[dict, str]:
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream',
        'MCP-Protocol-Version': '2025-03-26',
        'User-Agent': 'BERRY-LOCAL-MCP/1',
    }
    if session:
        headers['Mcp-Session-Id'] = session
    request = urllib.request.Request(_endpoint(), method='POST', headers=headers,
                                     data=json.dumps(message).encode('utf-8'))
    try:
        with OPENER.open(request, timeout=4) as response:
            if int(response.headers.get('Content-Length') or 0) > 250_000:
                raise OpenClipperError('Raspuns MCP prea mare')
            raw = response.read(250_001)
            if len(raw) > 250_000:
                raise OpenClipperError('Raspuns MCP prea mare')
            session_id = response.headers.get('Mcp-Session-Id', session)
            if not raw:
                return {}, session_id
            body = raw.decode('utf-8')
            if response.headers.get('Content-Type', '').startswith('text/event-stream'):
                # Streamable HTTP JSON-RPC event; keep the last data object.
                events = [line[5:].strip() for line in body.splitlines()
                          if line.startswith('data:')]
                if not events:
                    raise OpenClipperError('Raspuns MCP SSE gol')
                body = events[-1]
            result = json.loads(body)
            if not isinstance(result, dict):
                raise OpenClipperError('Raspuns MCP invalid')
            return result, session_id
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
            UnicodeError, json.JSONDecodeError) as exc:
        raise OpenClipperError('OpenClipper MCP indisponibil sau raspuns invalid') from exc


def status() -> dict:
    try:
        url = f'http://127.0.0.1:{_port()}/studio-import/health'
        with OPENER.open(urllib.request.Request(url, method='GET'), timeout=2) as resp:
            online = resp.status == 200
    except (OpenClipperError, urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        online = False
    return {
        'local_only': True, 'online': online,
        'transport': 'OpenClipper Streamable HTTP MCP',
        'read_only_tools': sorted(ALLOWED_TOOLS),
        'mutating_tools_enabled': False, 'social_publishing_enabled': False,
        'note': 'Porneste aplicatia desktop OpenClipper pe Windows pentru lista proiectelor',
    }


def list_local(kind: str) -> dict:
    if kind not in ALLOWED_TOOLS:
        raise OpenClipperError('Instrument MCP interzis')
    init, session = _call({
        'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
        'params': {'protocolVersion': '2025-03-26', 'capabilities': {},
                   'clientInfo': {'name': 'berry-ai-autopilot', 'version': '1.0'}}})
    if 'error' in init:
        raise OpenClipperError('OpenClipper a respins sesiunea MCP')
    _call({'jsonrpc': '2.0', 'method': 'notifications/initialized'}, session=session)
    result, _ = _call({
        'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call',
        'params': {'name': kind, 'arguments': {'skip': 0, 'rows': 20}}},
        session=session)
    if 'error' in result:
        raise OpenClipperError('OpenClipper a respins interogarea')
    blocks = (result.get('result') or {}).get('content') or []
    if not blocks or not isinstance(blocks[0].get('text'), str):
        raise OpenClipperError('OpenClipper nu a returnat lista')
    try:
        parsed = json.loads(blocks[0]['text'])
    except json.JSONDecodeError as exc:
        raise OpenClipperError('Lista OpenClipper nu este JSON valid') from exc
    if not isinstance(parsed, dict):
        raise OpenClipperError('Lista OpenClipper invalida')
    return {
        'source': 'OPENCLIPPER_LOCAL_MCP', 'tool': kind, 'data': parsed,
        'read_only': True, 'published': False, 'cloud_used': False,
    }
