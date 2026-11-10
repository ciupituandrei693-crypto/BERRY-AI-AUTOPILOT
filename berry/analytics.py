"""Offline analytics from user-exported platform CSVs. No platform API access."""
from __future__ import annotations
import csv
import hashlib
import io
import json
from datetime import datetime
from . import db

FIELDS = ('platform','channel_id','title','views','likes','comments','shares','watch_seconds','published_at')
PLATFORMS = ('youtube','instagram','tiktok')
CHANNEL_IDS = {c[0] for c in db.CHANNELS}


def init() -> None:
    with db.connection() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS analytics_entries (
          id INTEGER PRIMARY KEY AUTOINCREMENT, digest TEXT UNIQUE NOT NULL,
          platform TEXT NOT NULL, channel_id TEXT NOT NULL, title TEXT NOT NULL,
          views INTEGER NOT NULL, likes INTEGER NOT NULL, comments INTEGER NOT NULL,
          shares INTEGER NOT NULL, watch_seconds REAL NOT NULL,
          published_at TEXT NOT NULL, imported_at TEXT NOT NULL)''')


def import_csv(data: bytes) -> dict:
    if len(data) > 1_000_000:
        raise ValueError('CSV depășește 1 MB')
    try:
        decoded = data.decode('utf-8-sig')
    except UnicodeError as exc:
        raise ValueError('CSV trebuie să fie UTF-8') from exc
    reader = csv.DictReader(io.StringIO(decoded))
    if not reader.fieldnames or not set(FIELDS).issubset(set(reader.fieldnames)):
        raise ValueError('CSV necesită coloanele: ' + ', '.join(FIELDS))
    inserted = skipped = 0
    with db.connection() as con:
        for index, row in enumerate(reader, 1):
            if index > 1000:
                raise ValueError('Maximum 1000 rânduri per import')
            platform = (row['platform'] or '').strip().lower()
            channel = (row['channel_id'] or '').strip().lower()
            title = (row['title'] or '').strip()[:200]
            if platform not in PLATFORMS or channel not in CHANNEL_IDS or not title:
                raise ValueError(f'Rândul {index}: platformă/canal/titlu invalid')
            try:
                numbers = [int(row[key]) for key in ('views','likes','comments','shares')]
                watch = float(row['watch_seconds'])
                published = datetime.fromisoformat((row['published_at'] or '').strip())
            except (ValueError, TypeError, OverflowError) as exc:
                raise ValueError(f'Rândul {index}: valori numerice sau dată invalide') from exc
            if (any(n < 0 or n > 1_000_000_000 for n in numbers) or
                    not 0 <= watch <= 1_000_000_000 or published.tzinfo is None):
                raise ValueError(f'Rândul {index}: valori în afara limitelor sau lipsă fus orar')
            digest = hashlib.sha256(json.dumps([platform, channel, title, *numbers, watch,
                                                published.isoformat()], ensure_ascii=False).encode()).hexdigest()
            cur = con.execute('''INSERT OR IGNORE INTO analytics_entries
                (digest,platform,channel_id,title,views,likes,comments,shares,watch_seconds,published_at,imported_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)''',
                (digest, platform, channel, title, *numbers, watch, published.isoformat(), db.utcnow()))
            inserted += cur.rowcount
            skipped += 1 - cur.rowcount
        db.audit(con, 'manual_analytics_csv_import', {'inserted': inserted, 'duplicates': skipped})
    return {'imported': inserted, 'duplicates': skipped, 'source': 'USER_CSV', 'external_connections': False}


def report() -> dict:
    rows = db.all_rows('''SELECT channel_id,COUNT(*) posts,SUM(views) views,
       SUM(likes+comments+shares) interactions,SUM(watch_seconds) watch_seconds
       FROM analytics_entries GROUP BY channel_id ORDER BY views DESC''')
    for row in rows:
        row['engagement_percent'] = round(100 * row['interactions'] / max(1,row['views']), 2)
    recent = db.all_rows('''SELECT platform,channel_id,title,views,likes,comments,shares,watch_seconds,published_at
      FROM analytics_entries ORDER BY published_at DESC LIMIT 30''')
    suggestions = []
    for row in rows:
        if row['views'] < 100:
            suggestions.append(f"{row['channel_id']}: eșantion mic; evită concluziile despre performanță")
        elif row['engagement_percent'] < 2:
            suggestions.append(f"{row['channel_id']}: testează două variante de hook și thumbnail")
        elif row['engagement_percent'] > 6:
            suggestions.append(f"{row['channel_id']}: investighează temele cu interacțiuni ridicate")
    return {'source': 'USER_CSV', 'real_time': False, 'platform_connected': False,
            'channels': rows, 'recent': recent, 'suggestions': suggestions}
