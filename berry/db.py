"""Local-only SQLite persistence. The database is stored inside /data."""
from __future__ import annotations
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = Path(os.getenv('BERRY_DB_PATH', str(ROOT / 'data' / 'berry.sqlite3')))
CHANNELS = [
    ('mind','FRUIT MIND','Dark Psychology','MUREX','#9b5bf4','Psihologie, comportamente și limite sănătoase'),
    ('wealth','FRUIT WEALTH','Educație financiară','BANAN','#f9b548','Bani, economii, investiții: educație, nu recomandări'),
    ('beats','FRUIT BEATS','Muzică originală','AFINA STAR','#da7bff','Un singur fruct-solist și compoziții originale'),
    ('lab','FRUIT LAB','Știință','AFINA','#45bcfa','Experimente, explicații și descoperiri verificate'),
    ('heart','FRUIT HEART','Relații','EMERA & CHERO','#ff718e','Iubire, comunicare și povești emoționale'),
]
CHARACTERS = [
    ('MUREX','mind','Strugure mov închis; fedora, palton noir, costum','Misterios, calculat, atent la nuanțe','Masculină gravă'),
    ('BANAN','wealth','Banană galbenă; costum business, ochelari','Carismatic, explică simplu','Masculină energică'),
    ('AFINA STAR','beats','Afină violet-albăstruie; rochie cu paiete și microfon','Solistă pop expresivă','Feminină cântată, originală'),
    ('RUBY NOTE','beats','Măr roșu; ținută de scenă elegantă','Sensibil și dramatic','Baladă'),
    ('GOLD PINE','beats','Ananas auriu; haine de scenă spectaculoase','Showman energic','Funk / dance'),
    ('AFINA','lab','Afină ALBASTRĂ; halat alb, ochelari laborator, eprubetă','Cercetătoare curioasă și riguroasă','Feminină entuziastă'),
    ('EMERA','heart','Măr verde; rochie roșie, bijuterii aurii','Empatică, sigură pe sine','Feminină caldă'),
    ('CHERO','heart','Cireașă roșie; costum negru cu papion','Romantic, sincer','Masculină caldă'),
    ('BERRY','all','Căpșună roșie; gazdă premium','Coordonator al universului','Feminină clară'),
]

def utcnow():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

@contextmanager
def connection():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys = ON')
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def all_rows(sql, args=()):
    with connection() as con:
        return [dict(x) for x in con.execute(sql, args).fetchall()]

def one_row(sql, args=()):
    with connection() as con:
        v = con.execute(sql,args).fetchone()
        return dict(v) if v else None

def audit(con, action, detail):
    con.execute('INSERT INTO audit_log(time,action,detail) VALUES(?,?,?)',(utcnow(),action,json.dumps(detail,ensure_ascii=False)))

def init_db():
    with connection() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS channels(id TEXT PRIMARY KEY,name TEXT NOT NULL,niche TEXT NOT NULL,lead TEXT NOT NULL,color TEXT NOT NULL,description TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS characters(name TEXT PRIMARY KEY,channel_id TEXT NOT NULL,appearance TEXT NOT NULL,personality TEXT NOT NULL,voice TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS items(id INTEGER PRIMARY KEY AUTOINCREMENT,channel_id TEXT NOT NULL REFERENCES channels(id),content_type TEXT NOT NULL,topic TEXT NOT NULL,title TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'DRAFT',seo_json TEXT,media_filename TEXT,created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS batches(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'PENDING',created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS batch_items(batch_id INTEGER REFERENCES batches(id),item_id INTEGER REFERENCES items(id),PRIMARY KEY(batch_id,item_id));
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS daily_plans(day TEXT PRIMARY KEY,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS spend_proposals(id INTEGER PRIMARY KEY AUTOINCREMENT,category TEXT NOT NULL,channel_id TEXT,amount REAL NOT NULL,note TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'PENDING',created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY AUTOINCREMENT,time TEXT NOT NULL,action TEXT NOT NULL,detail TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS youtube_channel_plans(fruit_channel_id TEXT PRIMARY KEY REFERENCES channels(id), youtube_channel_id TEXT UNIQUE, display_label TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL);
        ''')
        for c in CHANNELS: con.execute('INSERT OR IGNORE INTO channels VALUES(?,?,?,?,?,?)',c)
        for c in CHARACTERS: con.execute('INSERT OR IGNORE INTO characters VALUES(?,?,?,?,?)',c)
        for k,v in {'kill_switch':'true','production_limit':'250','promo_per_channel':'100','mode':'SEMI_AUTOPILOT'}.items():
            con.execute('INSERT OR IGNORE INTO settings VALUES(?,?)',(k,v))
