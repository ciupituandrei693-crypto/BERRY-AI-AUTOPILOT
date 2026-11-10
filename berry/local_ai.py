"""Optional KoboldCpp text generator; loopback-only and no redirects/cloud fallback."""
from __future__ import annotations
from . import engines


class LocalAIError(Exception):
    pass


def generate_text(channel: str, topic: str, format_name: str) -> str:
    prompt = (
        'Ești BERRY, editor SEO pentru un studio cu personaje-fructe originale 3D. '
        'Compune în română: 1 hook de 2-3 secunde, 1 titlu, o descriere scurtă Instagram, '
        'o descriere TikTok, un titlu și o descriere YouTube, 5 hashtaguri relevante, '
        'un îndemn la acțiune. Fără promisiuni de vizualizări și fără a inventa date. '
        'Pentru muzică propune exclusiv compoziție originală. '
        f'Canal: {channel[:50]}. Format: {format_name[:50]}. Subiect: {topic[:250]}.\n'
        'Răspuns în secțiuni clar separate:\n'
    )
    try:
        obj = engines.json_request('koboldcpp', '/api/v1/generate', payload={
            'prompt': prompt, 'max_length': 350, 'temperature': 0.65}, timeout=35)
    except engines.EngineError as exc:
        raise LocalAIError('KoboldCpp nu este disponibil sau adresa nu este locală. Verifică motorul și încearcă din nou.') from exc
    result = obj.get('results', [])
    if not isinstance(result, list) or not result or not isinstance(result[0], dict):
        raise LocalAIError('Motorul local a trimis un răspuns neașteptat.')
    value = result[0].get('text', '')
    if not isinstance(value, str) or not value.strip():
        raise LocalAIError('Motorul nu a generat text.')
    return value.strip()[:6000]
