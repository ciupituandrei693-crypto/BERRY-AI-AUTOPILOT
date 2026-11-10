"""Optional KoboldCpp bridge. Only loopback addresses allowed, never cloud."""
from __future__ import annotations
import json
import os
import urllib.error
import urllib.request
from urllib.parse import urlparse

class LocalAIError(Exception):pass

def generate_text(channel:str,topic:str,format_name:str)->str:
    endpoint=os.environ.get('BERRY_KOBOLD_URL','http://127.0.0.1:5001').rstrip('/')
    u=urlparse(endpoint)
    if u.scheme!='http' or u.hostname not in ('127.0.0.1','localhost','::1') or u.username or u.password or u.path not in ('','/'):
        raise LocalAIError('Sunt permise numai adrese locale KoboldCpp (localhost).')
    prompt=(
      'Ești BERRY, editor SEO pentru un studio cu personaje-fructe originale 3D. '
      'Compune în română: 1 hook de 2-3 secunde, 1 titlu, o descriere scurtă Instagram, '
      'o descriere TikTok, un titlu și o descriere YouTube, 5 hashtaguri relevante, '
      'un îndemn la acțiune. Fără promisiuni de vizualizări și fără a inventa date. '
      'Pentru muzică propune exclusiv compoziție originală. '
      f'Canal: {channel[:50]}. Format: {format_name[:50]}. Subiect: {topic[:250]}.\n'
      'Răspuns în secțiuni clar separate:\n'
    )
    req=urllib.request.Request(endpoint+'/api/v1/generate',
          data=json.dumps({'prompt':prompt,'max_length':350,'temperature':0.65}).encode('utf-8'),
          headers={'Content-Type':'application/json'},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=35) as resp:
            if int(resp.headers.get('Content-Length','0') or 0)>1000000:
                raise LocalAIError('Răspunsul local este prea mare')
            obj=json.loads(resp.read(1000000))
    except (urllib.error.URLError,TimeoutError,ValueError) as exc:
        raise LocalAIError('KoboldCpp nu este disponibil pe PC. Pornește motorul local și încearcă din nou.') from exc
    result=obj.get('results',[{}])
    if not isinstance(result,list) or not result:
        raise LocalAIError('Motorul local a trimis un răspuns neașteptat.')
    s=result[0].get('text','')
    if not isinstance(s,str) or not s.strip():
        raise LocalAIError('Motorul nu a generat text.')
    return s.strip()[:6000]
