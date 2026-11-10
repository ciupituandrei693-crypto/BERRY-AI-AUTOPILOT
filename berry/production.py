"""Supervised, local-only sequential batch rendering. No external actions."""
from __future__ import annotations
import json
import threading
import time
from . import db, studio

START_LOCK = threading.Lock()
MAX_ITEMS = 30


def init() -> None:
    with db.connection() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS production_runs(
            id INTEGER PRIMARY KEY AUTOINCREMENT, status TEXT NOT NULL,
            items_json TEXT NOT NULL, total INTEGER NOT NULL, completed INTEGER NOT NULL DEFAULT 0,
            failed INTEGER NOT NULL DEFAULT 0, current_item_id INTEGER,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL)''')
        con.execute("UPDATE production_runs SET status='INTERRUPTED',updated_at=? WHERE status IN ('RUNNING','QUEUED')", (db.utcnow(),))


def runs() -> list[dict]:
    return db.all_rows('SELECT id,status,total,completed,failed,current_item_id,created_at,updated_at FROM production_runs ORDER BY id DESC LIMIT 20')


def start() -> dict:
    with START_LOCK:
        if db.one_row("SELECT id FROM production_runs WHERE status IN ('RUNNING','QUEUED')"):
            raise ValueError('Există deja o producție locală activă')
        ids = [r['id'] for r in db.all_rows('''SELECT i.id FROM items i WHERE i.status='DRAFT'
            AND NOT EXISTS(SELECT 1 FROM render_jobs j WHERE j.item_id=i.id AND j.mode='full' AND j.status='DONE')
            ORDER BY i.id LIMIT ?''', (MAX_ITEMS,))]
        if not ids:
            raise ValueError('Nu există fișe DRAFT fără randare FULL')
        now = db.utcnow()
        with db.connection() as con:
            cur = con.execute('INSERT INTO production_runs(status,items_json,total,created_at,updated_at) VALUES(?,?,?,?,?)',
                              ('QUEUED',json.dumps(ids),len(ids),now,now))
            run_id = cur.lastrowid
            db.audit(con,'local_production_queued',{'run_id':run_id,'items':len(ids)})
        threading.Thread(target=_worker,args=(run_id,ids),daemon=True,name=f'berry-production-{run_id}').start()
        return {'run_id':run_id,'total':len(ids),'status':'QUEUED','local_only':True}


def cancel(run_id: int) -> dict:
    with db.connection() as con:
        row = con.execute('SELECT status FROM production_runs WHERE id=?',(run_id,)).fetchone()
        if not row:
            raise LookupError('Producția nu există')
        if row['status'] not in ('RUNNING','QUEUED'):
            raise ValueError('Producția nu mai este activă')
        con.execute("UPDATE production_runs SET status='CANCEL_REQUESTED',updated_at=? WHERE id=?",(db.utcnow(),run_id))
        db.audit(con,'local_production_cancel_requested',{'run_id':run_id})
    return {'status':'CANCEL_REQUESTED','note':'Randarea în curs se termină înainte de oprire'}


def _worker(run_id: int, ids: list[int]) -> None:
    with db.connection() as con:
        con.execute("UPDATE production_runs SET status='RUNNING',updated_at=? WHERE id=?",(db.utcnow(),run_id))
    for item_id in ids:
        current = db.one_row('SELECT status FROM production_runs WHERE id=?',(run_id,))
        if not current or current['status']=='CANCEL_REQUESTED':
            with db.connection() as con:
                con.execute("UPDATE production_runs SET status='CANCELLED',updated_at=? WHERE id=?",(db.utcnow(),run_id))
            return
        failed = False
        try:
            job_id = studio.submit(item_id,'full')
            with db.connection() as con:
                con.execute('UPDATE production_runs SET current_item_id=?,updated_at=? WHERE id=?',(item_id,db.utcnow(),run_id))
            # Individual studio jobs have their own error handling and resource lock.
            while True:
                job = studio.get_job(job_id)
                if not job or job['status'] not in ('QUEUED','RUNNING'):
                    failed = not job or job['status'] != 'DONE'
                    break
                time.sleep(.4)
        except (LookupError,ValueError,RuntimeError):
            failed = True
        with db.connection() as con:
            con.execute('UPDATE production_runs SET completed=completed+1,failed=failed+?,updated_at=? WHERE id=?',
                        (int(failed),db.utcnow(),run_id))
    with db.connection() as con:
        con.execute("UPDATE production_runs SET status='FINISHED',current_item_id=NULL,updated_at=? WHERE id=?",(db.utcnow(),run_id))
        db.audit(con,'local_production_finished',{'run_id':run_id,'total':len(ids)})
