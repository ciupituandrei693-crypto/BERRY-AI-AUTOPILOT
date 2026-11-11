"""BERRY AI v1: LOCAL planning and approvals only, NO social posting or spend execution."""
from __future__ import annotations
import csv
import hmac
import io
import json
import os
import sqlite3
import io
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Literal
from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field
from . import db
from .seo import draft
from .local_ai import generate_text, LocalAIError
from . import studio, workflow, production, engines, creative, analytics, diagnostics, youtube_oauth, instagram_skill_tools, jarvis_api

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT/'static'
KEY = os.environ.get('BERRY_ACCESS_KEY','')
# Binding to a network interface without TLS/auth is not allowed in the starter launcher.

@asynccontextmanager
async def lifespan(app:FastAPI):
    db.init_db()
    studio.init_jobs()
    workflow.init()
    production.init()
    creative.init()
    analytics.init()
    jarvis_api.init()
    yield

app=FastAPI(title='BERRY AI — LOCAL',version='1.3.0-rc1',lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1','localhost','testserver'])
app.include_router(jarvis_api.router)

@app.middleware('http')
async def security_headers(request:Request,call_next):
    if request.url.path.startswith('/api/') and request.method not in ('GET', 'HEAD', 'OPTIONS'):
        origin = request.headers.get('origin')
        if origin and origin not in (f'http://{request.headers.get("host", "")}', f'https://{request.headers.get("host", "")}'):
            return JSONResponse({'detail': 'Origine nepermisă pentru operație locală'}, status_code=403)
    resp=await call_next(request)
    resp.headers['X-Content-Type-Options']='nosniff'
    resp.headers['X-Frame-Options']='DENY'
    resp.headers['Content-Security-Policy']="default-src 'self'; img-src 'self' data:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; object-src 'none'"
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
       'local_storyboard_preview_enabled':True,'local_motion_graphics_enabled':True,'local_calendar_enabled':True,'local_export_enabled':True,
       'notice':'v1.3 RC: bridge facial AI/3D local configurabil și teste PC; fără publicare, cloud sau costuri.'}

# --- Google/YouTube OAuth PREPARATION ONLY: no live authorization or upload. ---
class YoutubeChannelPlan(BaseModel):
    fruit_channel_id: Literal['mind', 'wealth', 'beats', 'lab', 'heart']
    youtube_channel_id: str | None = Field(default=None, pattern=r'^UC[A-Za-z0-9_-]{22}$')
    display_label: str = Field(default='', max_length=100)


@app.get('/api/integrations/youtube/plan', dependencies=[Depends(guarded)])
def youtube_oauth_plan():
    planned = {r['fruit_channel_id']: r for r in db.all_rows(
        'SELECT fruit_channel_id,youtube_channel_id,display_label,updated_at FROM youtube_channel_plans')}
    channels = []
    for fruit_id, name, *_ in db.CHANNELS:
        row = planned.get(fruit_id, {})
        channels.append({
            'fruit_channel_id': fruit_id,
            'fruit_name': name,
            'youtube_channel_id': row.get('youtube_channel_id'),
            'display_label': row.get('display_label', ''),
            'planned': bool(row),
            'verified': False,
            'connected': False,
            'can_publish': False,
        })
    return {**youtube_oauth.blueprint(), 'planned_count': len(planned), 'channels': channels}


@app.post('/api/integrations/youtube/channel-plan', dependencies=[Depends(guarded)], status_code=201)
def youtube_channel_plan(data: YoutubeChannelPlan):
    # This records user-entered metadata only. No Google API or token validation.
    now = db.utcnow()
    try:
        with db.connection() as con:
            con.execute('''INSERT INTO youtube_channel_plans(fruit_channel_id,youtube_channel_id,display_label,updated_at)
                           VALUES(?,?,?,?) ON CONFLICT(fruit_channel_id) DO UPDATE SET
                           youtube_channel_id=excluded.youtube_channel_id,
                           display_label=excluded.display_label,updated_at=excluded.updated_at''',
                        (data.fruit_channel_id, data.youtube_channel_id, data.display_label.strip(), now))
            db.audit(con, 'youtube_channel_plan_local_only',
                     {'fruit_channel_id': data.fruit_channel_id, 'verified': False, 'connected': False})
    except sqlite3.IntegrityError as exc:
        raise HTTPException(409, 'Acest canal YouTube este deja asociat în planul altui brand BERRY') from exc
    return {'saved': True, 'verified': False, 'connected': False, 'publishing_enabled': False}


@app.delete('/api/integrations/youtube/channel-plan/{fruit_channel_id}', dependencies=[Depends(guarded)])
def delete_youtube_channel_plan(fruit_channel_id: Literal['mind', 'wealth', 'beats', 'lab', 'heart']):
    with db.connection() as con:
        cur = con.execute('DELETE FROM youtube_channel_plans WHERE fruit_channel_id=?', (fruit_channel_id,))
        db.audit(con, 'youtube_channel_plan_removed_local_only', {'fruit_channel_id': fruit_channel_id})
    return {'deleted': bool(cur.rowcount), 'connected': False}


@app.get('/api/integrations/youtube/connect', dependencies=[Depends(guarded)])
def youtube_connect_locked():
    raise HTTPException(423, 'OAuth Google neactivat. Butonul de conectare rămâne blocat până la aprobare.')


@app.get('/api/integrations/youtube/callback', dependencies=[Depends(guarded)])
def youtube_callback_locked():
    # No token exchange, no persistence and no external API calls.
    raise HTTPException(423, 'Callback OAuth dezactivat; nu sunt acceptate coduri de autorizare.')


@app.post('/api/integrations/youtube/upload', dependencies=[Depends(guarded)])
def youtube_upload_locked():
    raise HTTPException(423, 'Încărcarea YouTube este dezactivată. Nu există permisiuni de publicare.')


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

class InstagramAnalysisInput(BaseModel):
    kind: Literal['hook', 'caption', 'beats']
    text: str = Field(min_length=1, max_length=5000)
    target_seconds: float = Field(default=15, ge=5, le=600)
    keywords: str = Field(default='', max_length=200)


@app.post('/api/seo/instagram/analyze', dependencies=[Depends(guarded)])
def instagram_offline_analysis(data: InstagramAnalysisInput):
    try:
        return instagram_skill_tools.analyze(
            data.kind, data.text, target=data.target_seconds, keywords=data.keywords)
    except instagram_skill_tools.InstagramToolError as exc:
        raise HTTPException(422, str(exc)) from exc


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


class RenderInput(BaseModel):
    item_id: int = Field(gt=0)
    mode: Literal['preview','full'] = 'preview'

@app.get('/api/studio/capabilities', dependencies=[Depends(guarded)])
def studio_capabilities():
    return {'version':'1.0.0-rc1','local_only':True,'components':studio.capabilities(),
            'render_kind':'STATIC_PREVIEW_OR_FULL_MOTION_GRAPHICS','ai_video_generated':False,
            'external_downloads':False,'social_posting':False,'cloud_gpu':False}

@app.get('/api/studio/jobs', dependencies=[Depends(guarded)])
def studio_jobs():
    return studio.get_jobs()

@app.post('/api/studio/render', status_code=202, dependencies=[Depends(guarded)])
def studio_render(data: RenderInput):
    try:
        job_id = studio.submit(data.item_id, data.mode)
    except LookupError as exc:
        raise HTTPException(404,str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409,str(exc)) from exc
    return {'job_id':job_id,'status':'QUEUED','mode':data.mode,
            'note':'Randare concept local; NU este video AI final și nu se publică.'}

@app.get('/api/studio/jobs/{job_id}', dependencies=[Depends(guarded)])
def studio_job(job_id:int):
    job=studio.get_job(job_id)
    if not job:raise HTTPException(404,'Randarea nu există')
    return job

@app.get('/api/studio/jobs/{job_id}/file/{kind}', dependencies=[Depends(guarded)])
def studio_download(job_id:int, kind:Literal['video','script','subtitles','manifest','image','voice','soundtrack']):
    path=studio.output_file(job_id,kind)
    if path is None:raise HTTPException(404,'Fișierul nu este disponibil')
    return FileResponse(path, filename=path.name)



class ScriptEdit(BaseModel):
    text: str = Field(min_length=20, max_length=20000)

@app.get('/api/items/{item_id}/script', dependencies=[Depends(guarded)])
def get_script(item_id: int):
    item = record('SELECT * FROM items WHERE id=?',(item_id,))
    script_root = Path(os.getenv('BERRY_SCRIPT_DIR', str(ROOT / 'data' / 'scripts')))
    custom = script_root / f'item_{item_id}.txt'
    text = custom.read_text(encoding='utf-8') if custom.is_file() else '\n'.join(studio._script_lines(item))
    return {'item_id':item_id,'text':text,'custom':custom.is_file(),'editable':item['status']=='DRAFT'}

@app.post('/api/items/{item_id}/script', dependencies=[Depends(guarded)])
def save_script(item_id: int, data: ScriptEdit):
    item = record('SELECT * FROM items WHERE id=?',(item_id,))
    if item['status'] != 'DRAFT':
        raise HTTPException(409,'Scriptul poate fi modificat doar în DRAFT')
    script_root = Path(os.getenv('BERRY_SCRIPT_DIR', str(ROOT / 'data' / 'scripts')))
    script_root.mkdir(parents=True,exist_ok=True)
    text='\n'.join(x.strip() for x in data.text.splitlines() if x.strip())+'\n'
    (script_root / f'item_{item_id}.txt').write_text(text,encoding='utf-8')
    with db.connection() as con:
        con.execute("UPDATE render_jobs SET status='STALE',updated_at=? WHERE item_id=? AND status IN ('DONE','PACKAGE_ONLY')",(db.utcnow(),item_id))
        db.audit(con,'script_changed',{'item_id':item_id,'length':len(text)})
    return {'saved':True,'item_id':item_id,'characters':len(text),'rerender_required':True}

class ReviewChecks(BaseModel):
    facts_checked: bool = False
    visual_rights: bool = False
    voice_rights: bool = False
    music_rights: bool = False
    disclosure_checked: bool = False
    notes: str = Field(default='', max_length=1000)

class ScheduleInput(BaseModel):
    item_id: int = Field(gt=0)
    platform: Literal['youtube','tiktok','instagram']
    scheduled_at: str = Field(min_length=20, max_length=40)

@app.get('/api/qa/{item_id}', dependencies=[Depends(guarded)])
def qa_status(item_id: int):
    try:
        return {'review': workflow.meta(item_id), 'report': workflow.quality(item_id)}
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc

@app.post('/api/qa/{item_id}/checks', dependencies=[Depends(guarded)])
def qa_checks(item_id: int, checks: ReviewChecks):
    try:
        return workflow.save_meta(item_id, checks.model_dump(), checks.notes)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc

@app.post('/api/qa/{item_id}/run', dependencies=[Depends(guarded)])
def qa_run(item_id: int):
    try:
        return workflow.quality(item_id, save=True)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc

@app.get('/api/calendar', dependencies=[Depends(guarded)])
def calendar_list():
    return workflow.calendar()

@app.post('/api/calendar', status_code=201, dependencies=[Depends(guarded)])
def calendar_add(data: ScheduleInput):
    try:
        return workflow.schedule(data.item_id, data.platform, data.scheduled_at)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc

@app.post('/api/calendar/{schedule_id}/cancel', dependencies=[Depends(guarded)])
def calendar_cancel(schedule_id: int):
    try:
        return workflow.cancel_schedule(schedule_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc

@app.get('/api/calendar/{schedule_id}/package', dependencies=[Depends(guarded)])
def calendar_package(schedule_id: int):
    try:
        content, filename = workflow.package(schedule_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return Response(content, media_type='application/zip', headers={'Content-Disposition':f'attachment; filename="{filename}"'})

@app.get('/api/backup', dependencies=[Depends(guarded)])
def backup_download():
    content, filename = workflow.backup()
    return Response(content, media_type='application/zip', headers={'Content-Disposition':f'attachment; filename="{filename}"'})


@app.get('/api/production/runs', dependencies=[Depends(guarded)])
def production_runs():
    return production.runs()

@app.post('/api/production/start', status_code=202, dependencies=[Depends(guarded)])
def production_start():
    try:
        return production.start()
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc

@app.post('/api/production/{run_id}/cancel', dependencies=[Depends(guarded)])
def production_cancel(run_id: int):
    try:
        return production.cancel(run_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc

@app.get('/api/production/summary', dependencies=[Depends(guarded)])
def production_summary():
    counts = {r['status']:r['n'] for r in db.all_rows('SELECT status,COUNT(*) n FROM items GROUP BY status')}
    jobs = {r['status']:r['n'] for r in db.all_rows('SELECT status,COUNT(*) n FROM render_jobs GROUP BY status')}
    return {'items':counts, 'renders':jobs, 'calendar':len(workflow.calendar()),
            'local_only':True, 'automatic_publishing':False, 'real_spend':False,
            'engine_requirements': 'Modele AI, Blender/ComfyUI și voci sunt opționale și nu sunt incluse'}

@app.post('/api/studio/render-next', status_code=202, dependencies=[Depends(guarded)])
def render_next():
    rows = db.all_rows("""SELECT i.id FROM items i WHERE i.status='DRAFT'
      AND NOT EXISTS(SELECT 1 FROM render_jobs j WHERE j.item_id=i.id AND j.mode='full' AND j.status='DONE')
      ORDER BY i.id LIMIT 1""")
    if not rows:
        return {'job_id':None,'message':'Toate schițele au randare completă sau nu există schițe'}
    try:
        job_id = studio.submit(rows[0]['id'], 'full')
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return {'job_id':job_id,'item_id':rows[0]['id'],'status':'QUEUED'}

@app.post('/api/items/{item_id}/art', dependencies=[Depends(guarded)])
async def upload_art(item_id: int, file: UploadFile = File(...)):
    from PIL import Image, ImageOps, UnidentifiedImageError
    item = record('SELECT * FROM items WHERE id=?', (item_id,))
    if item['status'] != 'DRAFT':
        raise HTTPException(409,'Importul este permis doar pentru DRAFT')
    raw = await file.read(8_000_001)
    if len(raw) > 8_000_000:
        raise HTTPException(413, 'Imagine prea mare (max. 8 MB)')
    try:
        with Image.open(io.BytesIO(raw)) as source:
            if source.format not in ('JPEG','PNG','WEBP'):
                raise ValueError('Formatul trebuie să fie JPEG, PNG sau WEBP')
            if source.width * source.height > 25_000_000:
                raise ValueError('Imagine prea mare în pixeli')
            picture = ImageOps.exif_transpose(source).convert('RGB')
            picture.thumbnail((2048,2048))
    except (UnidentifiedImageError, ValueError, OSError) as exc:
        raise HTTPException(422, 'Fișier imagine invalid') from exc
    assets = Path(os.getenv('BERRY_ASSET_DIR', str(ROOT / 'data' / 'assets')))
    assets.mkdir(parents=True,exist_ok=True)
    target = assets / f'item_{item_id}.webp'
    picture.save(target,format='WEBP',quality=90)
    (assets / f"item_{item_id}_art_source.json").unlink(missing_ok=True)
    with db.connection() as con:
        con.execute("UPDATE render_jobs SET status='STALE',updated_at=? WHERE item_id=? AND status IN ('DONE','PACKAGE_ONLY')",(db.utcnow(),item_id))
        db.audit(con,'user_art_uploaded',{'item_id':item_id,'bytes':len(raw)})
    return {'stored':True,'item_id':item_id,'filename':target.name,'source':'USER_SUPPLIED'}

@app.post('/api/items/{item_id}/soundtrack', dependencies=[Depends(guarded)])
async def upload_soundtrack(item_id: int, file: UploadFile = File(...)):
    item = record('SELECT * FROM items WHERE id=?',(item_id,))
    if item['status'] != 'DRAFT':
        raise HTTPException(409,'Importul este permis doar pentru DRAFT')
    raw = await file.read(25_000_001)
    if len(raw) > 25_000_000:
        raise HTTPException(413,'Audio prea mare (max. 25 MB)')
    # Validate container signatures; FFmpeg validates actual decodability during render.
    if raw.startswith(b'RIFF') and raw[8:12] == b'WAVE':
        ext='wav'
    elif raw.startswith(b'ID3') or (len(raw)>2 and raw[0]==0xff and (raw[1]&0xe0)==0xe0):
        ext='mp3'
    else:
        raise HTTPException(422,'Acceptăm doar WAV și MP3 valide')
    assets = Path(os.getenv('BERRY_ASSET_DIR', str(ROOT / 'data' / 'assets')))
    assets.mkdir(parents=True,exist_ok=True)
    for old in assets.glob(f'item_{item_id}_soundtrack.*'):
        old.unlink(missing_ok=True)
    target=assets/f'item_{item_id}_soundtrack.{ext}'
    target.write_bytes(raw)
    (assets / f"item_{item_id}_music_source.json").unlink(missing_ok=True)
    with db.connection() as con:
        con.execute("UPDATE render_jobs SET status='STALE',updated_at=? WHERE item_id=? AND status IN ('DONE','PACKAGE_ONLY')",(db.utcnow(),item_id))
        db.audit(con,'user_soundtrack_uploaded',{'item_id':item_id,'bytes':len(raw),'format':ext})
    return {'stored':True,'item_id':item_id,'filename':target.name,'source':'USER_SUPPLIED'}

class CreativeStart(BaseModel):
    item_id: int = Field(gt=0)
    engine: Literal['comfyui','ace_step','wangp','faster_whisper','voice_studio','blender_3d','liveportrait','musetalk','latentsync','hunyuan3d']

@app.get('/api/engines', dependencies=[Depends(guarded)])
def local_engines():
    return {'local_only': True, 'automatic_install': False, 'cloud': False,
            'external_server': False, 'engines': engines.statuses()}

@app.get('/api/local/diagnostics', dependencies=[Depends(guarded)])
def local_diagnostics():
    return diagnostics.report()

@app.get('/api/ai/jobs', dependencies=[Depends(guarded)])
def ai_jobs():
    return creative.jobs()

@app.post('/api/ai/jobs', status_code=202, dependencies=[Depends(guarded)])
def ai_start(data: CreativeStart):
    try:
        return creative.start(data.item_id, data.engine)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc

@app.post('/api/items/{item_id}/voice', dependencies=[Depends(guarded)])
async def upload_voice(item_id: int, file: UploadFile = File(...)):
    item = record('SELECT * FROM items WHERE id=?', (item_id,))
    if item['status'] != 'DRAFT':
        raise HTTPException(409, 'Vocea se poate importa doar în DRAFT')
    raw = await file.read(25_000_001)
    if len(raw) > 25_000_000:
        raise HTTPException(413, 'Vocea depășește 25 MB')
    if raw.startswith(b'RIFF') and raw[8:12] == b'WAVE':
        ext = 'wav'
    elif raw.startswith(b'ID3') or (len(raw)>2 and raw[0]==255 and (raw[1]&224)==224):
        ext = 'mp3'
    else:
        raise HTTPException(422, 'Importă voce WAV sau MP3')
    root = creative.assets_dir()
    for old in root.glob(f'item_{item_id}_voice.*'):
        old.unlink(missing_ok=True)
    target = root / f'item_{item_id}_voice.{ext}'
    target.write_bytes(raw)
    creative._invalidate(item_id, 'USER_VOICE')
    return {'stored': True, 'filename': target.name, 'source': 'USER_SUPPLIED', 'review_required': True}

@app.post('/api/items/{item_id}/video', dependencies=[Depends(guarded)])
async def upload_video(item_id: int, file: UploadFile = File(...)):
    item = record('SELECT * FROM items WHERE id=?', (item_id,))
    if item['status'] != 'DRAFT':
        raise HTTPException(409, 'Video se poate importa doar în DRAFT')
    if item['content_type'] == 'image':
        raise HTTPException(422, 'Pentru fișele IMAGE încarcă o imagine')
    import tempfile
    ffmpeg = studio.binary_path('ffmpeg', 'BERRY_FFMPEG_PATH')
    if not ffmpeg:
        raise HTTPException(409, 'FFmpeg este necesar pentru verificarea video')
    root = creative.assets_dir()
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=root, prefix='berry_upload_', suffix='.mp4', delete=False) as tmp:
            temp_path = Path(tmp.name)
            size = 0
            first = b''
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > 150_000_000:
                    raise HTTPException(413, 'Video depășește 150 MB')
                if not first:
                    first = chunk[:64]
                tmp.write(chunk)
        if len(first) < 12 or first[4:8] != b'ftyp':
            raise HTTPException(422, 'Fișierul nu este MP4 valid')
        import subprocess
        try:
            check = subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-i', str(temp_path),
                                    '-frames:v', '1', '-f', 'null', '-'],
                                   capture_output=True, timeout=40, check=False)
        except subprocess.TimeoutExpired as exc:
            raise HTTPException(422, 'Verificarea video a expirat') from exc
        if check.returncode:
            raise HTTPException(422, 'FFmpeg nu poate decoda primul cadru')
        target = root / f'item_{item_id}_video.mp4'
        temp_path.replace(target)
        (root / f"item_{item_id}_video_source.json").unlink(missing_ok=True)
        temp_path = None
        creative._invalidate(item_id, 'USER_VIDEO')
        return {'stored': True, 'filename': target.name, 'source': 'USER_SUPPLIED', 'review_required': True}
    finally:
        if temp_path:
            temp_path.unlink(missing_ok=True)

@app.get('/api/analytics', dependencies=[Depends(guarded)])
def local_analytics():
    return analytics.report()

@app.post('/api/analytics/import', dependencies=[Depends(guarded)])
async def analytics_import(file: UploadFile = File(...)):
    data = await file.read(1_000_001)
    try:
        return analytics.import_csv(data)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@app.get('/api/integrations',dependencies=[Depends(guarded)])
def integrations():return {'instagram':'NOT_CONNECTED','tiktok':'NOT_CONNECTED','youtube':'NOT_CONNECTED','gpu':'DISABLED','external_server':'DISABLED', 'local_ai':'OPTIONAL_LOCAL_ENGINES','status':'REMOTE_AND_SOCIAL_FINAL_PHASE_ONLY'}

@app.get('/')
def home():return FileResponse(STATIC/'index.html')

app.mount('/static',StaticFiles(directory=STATIC),name='static')
