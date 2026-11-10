"""BERRY AI v1: LOCAL planning and approvals only, NO social posting or spend execution."""
from __future__ import annotations
import csv
import hmac
import io
import json
import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Literal
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from . import db
from .seo import draft
from .local_ai import generate_text, LocalAIError

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT/'static'
KEY = os.environ.get('BERRY_ACCESS_KEY','')
# Binding to a network interface without TLS/auth is not allowed in the starter launcher.

@asynccontextmanager
async def lifespan(app:FastAPI):
    db.init_db()
    yield

app=FastAPI(title='BERRY AI — LOCAL',version='0.1.0',lifespan=lifespan)

@app.middleware('http')
async def security_headers(request:Request,call_next):
    resp=await call_next(request)
    resp.headers['X-Content-Type-Options']='nosniff'
    resp.headers['X-Frame-Options']='DENY'
    resp.headers['Referrer-Policy']='no-referrer'
    resp.headers['Cache-Control']='no-store' if request.url.path.startswith('/api') else 'private, max-age=60'
    return resp

def guarded(request:Request):
    if KEY and not hmac.compare_digest(request.headers.get('X-BERRY-KEY',''),KEY):
        raise HTTPException(401,'Cheie de acces invalidă')

def record(sql:str,args:tuple=()):
    r=db.one_row(sql,args)
    if r is None: raise HTTPException(404,'Resursa nu există')
    return r

def settings_dict():
    return {r['key']:r['value'] for r in db.all_rows('SELECT * FROM settings')}

class ItemNew(BaseModel):
    channel_id: Literal['mind','wealth','beats','lab','heart']
    content_type: Literal['main90','short15','image','longform']
    topic: str=Field(min_length=3,max_length=300)
    title: str=Field(default='',max_length=200)

class SeoInput(BaseModel):
    channel_id: Literal['mind','wealth','beats','lab','heart']
    content_type: Literal['main90','short15','image','longform']
    topic: str=Field(min_length=3,max_length=300)

class BatchInput(BaseModel):
    name:str=Field(min_length=3,max_length=150)
    item_ids:list[int]=Field(min_length=1,max_length=100)

class Toggle(BaseModel):
    enabled:bool

class Spend(BaseModel):
    category:Literal['GPU','ADS','OTHER']
    channel_id:Literal['mind','wealth','beats','lab','heart']|None=None
    amount:float=Field(gt=0,le=100000)
    note:str=Field(min_length=4,max_length=350)

@app.get('/api/status',dependencies=[Depends(guarded)])
def get_status():
    cfg=settings_dict()
    return {'channels':5,'mode':cfg['mode'],'kill_switch':cfg['kill_switch']=='true',
       'items':db.one_row('SELECT COUNT(*) n FROM items')['n'],
       'pending_batches':db.one_row("SELECT COUNT(*) n FROM batches WHERE status='PENDING'")['n'],
       'production_limit':float(cfg['production_limit']),
       'promo_per_channel':float(cfg['promo_per_channel']),
       'social_connections':0,'gpu_connections':0,'external_server':False,
       'real_publication_enabled':False,'real_ai_video_enabled':False,
       'notice':'Versiune locală: doar planificare, SEO-model, aprobări. Fără conectare la conturi, GPU sau publicare.'}

@app.get('/api/channels',dependencies=[Depends(guarded)])
def channels(): return db.all_rows('SELECT * FROM channels')

@app.get('/api/characters',dependencies=[Depends(guarded)])
def characters():return db.all_rows('SELECT * FROM characters')

@app.get('/api/items',dependencies=[Depends(guarded)])
def items(channel_id:str|None=None):
    sql='SELECT * FROM items'
    args=[]
    if channel_id:
        sql+=' WHERE channel_id=?';args.append(channel_id)
    rows=db.all_rows(sql+' ORDER BY id DESC',args)
    for r in rows: r['seo']=json.loads(r.pop('seo_json')) if r['seo_json'] else None
    return rows

@app.post('/api/seo/preview',dependencies=[Depends(guarded)])
def seo_preview(data:SeoInput):
    try:return draft(data.channel_id,data.topic,data.content_type)
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc

@app.post('/api/seo/local-ai',dependencies=[Depends(guarded)])
def local_ai_seo(data:SeoInput):
    try:
        text = generate_text(data.channel_id,data.topic,data.content_type)
    except LocalAIError as exc:
        raise HTTPException(503,str(exc)) from exc
    return {'mode':'LOCAL_KOBOLDCPP','generated':text,'published':False,'warning':'Verifică manual adevărul, drepturile muzicale și formulările înainte de folosire.'}

@app.post('/api/items',status_code=201,dependencies=[Depends(guarded)])
def add_item(data:ItemNew):
    seo=draft(data.channel_id,data.topic,data.content_type)
    now=db.utcnow()
    with db.connection() as con:
        cur=con.execute('INSERT INTO items(channel_id,content_type,topic,title,seo_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?)',
             (data.channel_id,data.content_type,data.topic,data.title.strip() or seo['title'],json.dumps(seo,ensure_ascii=False),now,now))
        idx=cur.lastrowid
        db.audit(con,'item_created',{'id':idx,'channel':data.channel_id})
    return {'id':idx,'seo':seo,'status':'DRAFT'}

@app.post('/api/items/{item_id}/refresh-seo',dependencies=[Depends(guarded)])
def refresh_seo(item_id:int):
    r=record('SELECT * FROM items WHERE id=?',(item_id,))
    if r['status']!='DRAFT':raise HTTPException(409,'Doar materialele DRAFT pot fi modificate')
    new=draft(r['channel_id'],r['topic'],r['content_type'])
    with db.connection() as con:
        con.execute('UPDATE items SET seo_json=?,updated_at=? WHERE id=?',(json.dumps(new,ensure_ascii=False),db.utcnow(),item_id))
        db.audit(con,'seo_refreshed',{'item_id':item_id})
    return {'seo':new}

@app.delete('/api/items/{item_id}',dependencies=[Depends(guarded)])
def delete_item(item_id:int):
    r=record('SELECT * FROM items WHERE id=?',(item_id,))
    if r['status']!='DRAFT':raise HTTPException(409,'Nu se pot șterge materiale aprobate sau incluse într-un lot')
    if db.one_row('SELECT * FROM batch_items WHERE item_id=?',(item_id,)):
        raise HTTPException(409,'Materialul aparține unui lot')
    with db.connection() as con:
        con.execute('DELETE FROM items WHERE id=?',(item_id,));db.audit(con,'item_deleted',{'id':item_id})
    return {'deleted':True}

class PlanDay(BaseModel):
    day:date

DAY_TOPICS={
 'mind':['Când încrederea devine control','Cum recunoști manipularea prin vinovăție','Prietenul care ascunde adevărul','Limitele sănătoase într-un grup','Cum înțelegi semnalele ambigue'],
 'wealth':['Bugetul lunar al unui începător','Efectul cheltuielilor mici repetate','Economiile pentru primul obiectiv','Diferența dintre datorii și active','De ce contează fondul de urgență'],
 'beats':['O melodie originală despre un nou început','Un refren original despre curaj','O baladă originală despre prietenie','Un cântec original despre speranță','Un hit dance original despre reușită'],
 'lab':['De ce stelele strălucesc','Cum se formează un curcubeu','Ce se întâmplă în interiorul unei celule','De ce plutește gheața pe apă','Cum comunică albinele'],
 'heart':['Un mesaj care schimbă o relație','O promisiune testată de timp','O relație construită pe încredere','Cum ne cerem scuze sincer','Un gest mic care vindecă o neînțelegere'],
}

@app.post('/api/plan/day',dependencies=[Depends(guarded)],status_code=201)
def plan_day(data:PlanDay):
    if data.day.weekday()>4:
        raise HTTPException(422,'Programul este luni–vineri; alege o zi lucrătoare')
    day=data.day.isoformat()
    if db.one_row('SELECT * FROM daily_plans WHERE day=?',(day,)):
        raise HTTPException(409,'Există deja o planificare pentru această zi')
    now=db.utcnow(); count=0
    try:
        with db.connection() as con:
            con.execute('INSERT INTO daily_plans(day,created_at) VALUES(?,?)',(day,now))
            for c in db.CHANNELS:
                cid=c[0]; topic=DAY_TOPICS[cid][(data.day.toordinal()+len(cid))%5]
                # 1x video principal, 1x short și 3x imagini, toate în DRAFT
                for typ,suffix in [('main90','Video 90s'),('short15','Short 15s'),('image','Imagine promo 1'),('image','Imagine promo 2'),('image','Imagine promo 3')]:
                    title=f'{day} · {suffix} · {topic}'
                    seo=draft(cid,topic,typ)
                    con.execute('INSERT INTO items(channel_id,content_type,topic,title,seo_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?)',
                       (cid,typ,topic,title,json.dumps(seo,ensure_ascii=False),now,now))
                    count+=1
            db.audit(con,'daily_plan_created_local_only',{'day':day,'items':count,'media_generated':False})
    except sqlite3.IntegrityError:
        raise HTTPException(409,'Planificarea există deja')
    return {'day':day,'items_created':count,'media_generated':False,'status':'DRAFTS_ONLY'}

@app.get('/api/batches',dependencies=[Depends(guarded)])
def batches():
    rows=db.all_rows('SELECT * FROM batches ORDER BY id DESC')
    for row in rows:
        row['items']=db.all_rows('SELECT i.* FROM items i JOIN batch_items bi ON bi.item_id=i.id WHERE bi.batch_id=?',(row['id'],))
    return rows

@app.post('/api/batches',status_code=201,dependencies=[Depends(guarded)])
def add_batch(data:BatchInput):
    ids=list(dict.fromkeys(data.item_ids))
    found=db.all_rows('SELECT id,status FROM items WHERE id IN (%s)'%(','.join('?' for _ in ids)),ids)
    if len(found)!=len(ids) or any(r['status']!='DRAFT' for r in found):
        raise HTTPException(409,'Toate materialele trebuie să existe și să fie DRAFT')
    now=db.utcnow()
    with db.connection() as con:
        cur=con.execute('INSERT INTO batches(name,created_at,updated_at) VALUES(?,?,?)',(data.name,now,now))
        b=cur.lastrowid
        con.executemany('INSERT INTO batch_items(batch_id,item_id) VALUES(?,?)',[(b,i) for i in ids])
        con.executemany("UPDATE items SET status='IN_REVIEW',updated_at=? WHERE id=?",[(now,i) for i in ids])
        db.audit(con,'batch_created',{'batch_id':b,'ids':ids})
    return {'id':b,'status':'PENDING','items':ids}

@app.post('/api/batches/{batch_id}/approve',dependencies=[Depends(guarded)])
def approve(batch_id:int):
    b=record('SELECT * FROM batches WHERE id=?',(batch_id,))
    if b['status']!='PENDING':raise HTTPException(409,'Lotul nu mai așteaptă aprobare')
    now=db.utcnow()
    with db.connection() as con:
        con.execute("UPDATE batches SET status='APPROVED_NOT_PUBLISHED', updated_at=? WHERE id=?",(now,batch_id))
        con.execute("UPDATE items SET status='APPROVED_NOT_PUBLISHED',updated_at=? WHERE id IN (SELECT item_id FROM batch_items WHERE batch_id=?)",(now,batch_id))
        db.audit(con,'batch_approved_local_only',{'batch_id':batch_id,'published':False})
    return {'status':'APPROVED_NOT_PUBLISHED','published':False,'reason':'Nu există integrare API socială în această etapă.'}

@app.post('/api/batches/{batch_id}/reject',dependencies=[Depends(guarded)])
def reject(batch_id:int):
    b=record('SELECT * FROM batches WHERE id=?',(batch_id,))
    if b['status']!='PENDING':raise HTTPException(409,'Lotul nu mai așteaptă aprobare')
    now=db.utcnow()
    with db.connection() as con:
        con.execute("UPDATE batches SET status='REJECTED',updated_at=? WHERE id=?",(now,batch_id))
        con.execute("UPDATE items SET status='DRAFT',updated_at=? WHERE id IN (SELECT item_id FROM batch_items WHERE batch_id=?)",(now,batch_id))
        db.audit(con,'batch_rejected',{'batch_id':batch_id})
    return {'status':'REJECTED'}

@app.post('/api/settings/kill-switch',dependencies=[Depends(guarded)])
def set_kill_switch(t:Toggle):
    with db.connection() as con:
        con.execute('UPDATE settings SET value=? WHERE key=?',('true' if t.enabled else 'false','kill_switch'))
        db.audit(con,'kill_switch',{'active':t.enabled})
    return {'kill_switch':t.enabled,'outbound_publication_available':False}

@app.get('/api/budget',dependencies=[Depends(guarded)])
def budget():
    cfg=settings_dict()
    proposals=db.all_rows('SELECT * FROM spend_proposals ORDER BY id DESC')
    return {'production_limit':float(cfg['production_limit']),'marketing_per_brand':float(cfg['promo_per_channel']),
        'monthly_ads_total':5*float(cfg['promo_per_channel']),'monthly_target_total':float(cfg['production_limit'])+5*float(cfg['promo_per_channel']),
        'actual_spend_recorded':0,'spend_executed_by_app':0,'proposals':proposals}

@app.post('/api/spend-proposals',dependencies=[Depends(guarded)],status_code=201)
def propose_spend(p:Spend):
    if p.category=='ADS' and not p.channel_id:raise HTTPException(422,'Alege un canal pentru reclamă')
    with db.connection() as con:
        cur=con.execute('INSERT INTO spend_proposals(category,channel_id,amount,note,created_at) VALUES(?,?,?,?,?)',
           (p.category,p.channel_id,p.amount,p.note,db.utcnow()))
        db.audit(con,'spend_proposed_no_charge',{'proposal_id':cur.lastrowid,'amount':p.amount})
        return {'id':cur.lastrowid,'status':'PENDING','charged':False}

@app.get('/api/audit',dependencies=[Depends(guarded)])
def journal():return db.all_rows('SELECT * FROM audit_log ORDER BY id DESC LIMIT 100')

@app.get('/api/export.csv',dependencies=[Depends(guarded)])
def export_csv():
    out=io.StringIO();cols=['id','channel_id','content_type','topic','title','status','created_at']
    w=csv.DictWriter(out,fieldnames=cols);w.writeheader()
    for r in db.all_rows('SELECT '+','.join(cols)+' FROM items ORDER BY id'):w.writerow(r)
    return Response('\ufeff'+out.getvalue(),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename="berry_content.csv"'})

@app.get('/api/integrations',dependencies=[Depends(guarded)])
def integrations():return {'instagram':'NOT_CONNECTED','tiktok':'NOT_CONNECTED','youtube':'NOT_CONNECTED','gpu':'DISABLED','external_server':'DISABLED', 'local_ai':'NOT_CONNECTED','status':'FINAL_PHASE_ONLY'}

@app.get('/')
def home():return FileResponse(STATIC/'index.html')

app.mount('/static',StaticFiles(directory=STATIC),name='static')
