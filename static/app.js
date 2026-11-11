'use strict';
let state={status:{},channels:[],characters:[],items:[],batches:[],budget:{},audit:[],view:'overview'};
const $=s=>document.querySelector(s);
const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const names={mind:'FRUIT MIND',wealth:'FRUIT WEALTH',beats:'FRUIT BEATS',lab:'FRUIT LAB',heart:'FRUIT HEART'};
const images={mind:'mind.webp',wealth:'wealth.webp',beats:'beats.webp',lab:'lab.webp',heart:'heart.webp'};
const types={main90:'Video 90s',short15:'Short 15s',image:'Imagine',longform:'YouTube 5–10 min'};
const key=()=>sessionStorage.getItem('berry_key')||'';
async function api(url,method='GET',body){const opts={method,headers:{}};if(key())opts.headers['X-BERRY-KEY']=key();if(body!==undefined){opts.headers['Content-Type']='application/json';opts.body=JSON.stringify(body)}const r=await fetch('/api'+url,opts);if(r.status===401){const k=prompt('Introdu BERRY_ACCESS_KEY configurată local:');if(k){sessionStorage.setItem('berry_key',k);return api(url,method,body)}}if(!r.ok){let t;try{t=await r.json()}catch{t={detail:r.statusText}};throw new Error(t.detail||'Eroare')}if(r.headers.get('content-type')?.includes('application/json'))return r.json();return r.text()}
let toastTimer;function toast(msg){const el=$('#toast');el.textContent=msg;el.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove('show'),3300)}
function go(page){if(!$('#page-'+page))return;state.view=page;document.querySelectorAll('.page').forEach(x=>x.classList.toggle('active',x.id==='page-'+page));document.querySelectorAll('.nav-btn').forEach(x=>x.classList.toggle('active',x.dataset.page===page));$('#view-title').textContent=({overview:'Prezentare generală',channels:'Biblioteca de personaje',planner:'Content Planner',seo:'SEO Studio',approvals:'Approval Center',budgets:'Budget Guard',integrations:'Integrări & securitate',studio:'Media Studio',qa:'Quality & Rights QA',calendar:'Calendar & Export','ai-local':'AI Local Engines',analytics:'Analytics offline'})[page];window.scrollTo({top:0,behavior:'smooth'})}
window.go=go;
async function load(){try{const [status,channels,characters,items,batches,budget,audit]=await Promise.all([api('/status'),api('/channels'),api('/characters'),api('/items'),api('/batches'),api('/budget'),api('/audit')]);Object.assign(state,{status,channels,characters,items,batches,budget,audit});render()}catch(e){toast(e.message)}}
function opts(){for(const id of ['#new-channel','#seo-channel','#filter-channel','#spend-channel']){const sel=$(id),old=sel.value,empty=id.includes('filter')?'<option value="">Toate canalele</option>':id.includes('spend')?'<option value="">Niciun canal (pentru GPU/general)</option>':'';sel.innerHTML=empty+state.channels.map(c=>`<option value="${esc(c.id)}">${esc(c.name)}</option>`).join('');if([...sel.options].some(o=>o.value===old))sel.value=old}}
function render(){opts();$('#metric-channels').textContent=state.status.channels;$('#metric-items').textContent=state.status.items;$('#metric-batches').textContent=state.status.pending_batches;$('#kill-overview').textContent=state.status.kill_switch?'Activ':'Inactiv';$('#kill-overview').style.color=state.status.kill_switch?'#62dbb4':'#efa5af';$('#mode-pill').textContent=state.status.mode.replaceAll('_',' ');$('#kill-toggle').textContent=state.status.kill_switch?'Dezactivează comutatorul':'ACTIVEAZĂ KILL SWITCH';renderChannels();renderItems();renderBatches();renderBudget();renderAudit();renderStudioItems();renderWorkflowSelectors()}
function renderChannels(){const c=state.channels;$('#overview-channels').innerHTML=c.map(x=>`<div class="channel-card"><img src="/static/img/${images[x.id]}" alt="${esc(x.lead)}"><div class="content"><h3 style="color:${esc(x.color)}">${esc(x.name)}</h3><div class="niche">${esc(x.niche)}</div><div class="lead">● ${esc(x.lead)}</div></div></div>`).join('');$('#channel-detail').innerHTML=c.map(x=>`<div class="profile"><img src="/static/img/${images[x.id]}" alt="${esc(x.lead)}"><div><h3 style="color:${esc(x.color)}">${esc(x.name)}</h3><div class="meta">${esc(x.niche)} · ${esc(x.lead)}</div><p>${esc(x.description)}</p>${state.characters.filter(a=>a.channel_id===x.id).map(a=>`<p><strong>${esc(a.name)}</strong> — ${esc(a.appearance)}<br><span class="muted">${esc(a.personality)} · Voce: ${esc(a.voice)}</span></p>`).join('')}</div></div>`).join('')}
function renderItems(){const filter=$('#filter-channel').value;const rows=state.items.filter(x=>!filter||x.channel_id===filter);$('#items-list').innerHTML=rows.length?rows.map(x=>`<label class="item-row"><input type="checkbox" class="item-select" value="${x.id}" ${x.status!=='DRAFT'?'disabled':''}><span class="item-main"><strong>${esc(x.title)}</strong><small>${esc(names[x.channel_id])} · ${esc(types[x.content_type])} · ${esc(x.status)}</small><small>${esc(x.topic)}</small></span><span class="tag">#${x.id}</span></label>`).join(''):'<div class="empty">Nu există materiale. Creează primul episod în stânga.</div>'}
function renderBatches(){$('#batches-list').innerHTML=state.batches.length?state.batches.map(b=>`<div class="batch-panel"><div class="row-between"><h3>📋 ${esc(b.name)}</h3><span class="pill neutral">${esc(b.status)}</span></div><small class="muted">Lot #${b.id} · ${b.items.length} materiale · ${esc(b.created_at)}</small><details><summary>Conținutul lotului</summary>${b.items.map(x=>`<div>${esc(names[x.channel_id])} — ${esc(x.title)}</div>`).join('')}</details>${b.status==='PENDING'?`<div class="row-between"><span class="muted small">Aprobare locală, nu publicare</span><div class="buttons"><button class="btn small outline" onclick="changeBatch(${b.id},'reject')">Respinge</button><button class="btn small primary" onclick="changeBatch(${b.id},'approve')">Aprobă lotul</button></div></div>`:''}</div>`).join(''):'<div class="empty">Niciun lot. Selectează materiale DRAFT din Content Planner și trimite-le la aprobare.</div>'}
function renderBudget(){$('#proposals-list').innerHTML=state.budget.proposals?.length?state.budget.proposals.map(p=>`<div class="item-row"><div class="item-main"><strong>$${esc(p.amount.toFixed(2))} · ${esc(p.category)}</strong><small>${esc(p.channel_id||'General')} • ${esc(p.status)} • ${esc(p.created_at)}</small><small>${esc(p.note)}</small></div></div>`).join(''):'<div class="empty">Nicio propunere de cheltuială.</div>'}
function renderAudit(){$('#audit-list').innerHTML=state.audit.length?state.audit.map(a=>`<div class="audit-entry">${esc(a.time)} · <strong>${esc(a.action)}</strong></div>`).join(''):'<div class="empty">Jurnal gol.</div>'}
window.changeBatch=async(id,action)=>{if(action==='approve'&&!confirm('Aprobi doar în baza locală, fără publicare online. Continui?'))return;try{await api(`/batches/${id}/${action}`,'POST');toast(action==='approve'?'Aprobat local. NU a fost publicat.':'Lot respins; materialele revin în DRAFT');await load()}catch(e){toast(e.message)}};
$('#nav').addEventListener('click',e=>{const b=e.target.closest('[data-page]');if(b)go(b.dataset.page)});
$('#refresh').onclick=load;
$('#filter-channel').onchange=renderItems;
$('#select-drafts').onclick=()=>document.querySelectorAll('.item-select:not(:disabled)').forEach(el=>el.checked=true);
$('#day-plan').onclick=async()=>{const day=prompt('Data locală pentru plan (AAAA-LL-ZZ, doar luni–vineri):',new Date().toLocaleDateString('sv-SE'));if(!day)return;try{const r=await api('/plan/day','POST',{day});toast(`Au fost create ${r.items_created} fișe DRAFT pentru ${r.day}. Fără media reale.`);await load()}catch(e){toast(e.message)}};
$('#new-item').onsubmit=async e=>{e.preventDefault();try{const body={channel_id:$('#new-channel').value,content_type:$('#new-type').value,topic:$('#new-topic').value};const res=await api('/items','POST',body);toast(`Material #${res.id} creat cu SEO propus`);$('#new-topic').value='';await load()}catch(err){toast(err.message)}};
$('#seo-form').onsubmit=async e=>{e.preventDefault();try{const v=await api('/seo/preview','POST',{channel_id:$('#seo-channel').value,content_type:$('#seo-type').value,topic:$('#seo-topic').value});const parts=[['Hook',v.hook],['Titlu',v.title],['Instagram',v.instagram.caption],['TikTok',v.tiktok.caption],['YouTube — descriere',v.youtube.description],['Hashtaguri',v.hashtags.join(' ')],['Prompt personaj',v.character_prompt],['Prompt video',v.video_prompt],['Verificări',v.review_warning]];$('#seo-results').innerHTML='<h3>✦ Pachet SEO propus</h3>'+parts.map(([t,s])=>`<div class="seo-section"><h4>${esc(t)}</h4><pre>${esc(s)}</pre></div>`).join('')+'<button class="btn outline small" id="copy-seo">Copiază textul</button>';$('#copy-seo').onclick=()=>{navigator.clipboard?.writeText(parts.map(p=>p.join('\n')).join('\n\n')).then(()=>toast('Copiat!')).catch(()=>toast('Copiere indisponibilă în acest browser'))}}catch(err){toast(err.message)}};
$('#seo-local-ai').onclick=async()=>{try{const v=await api('/seo/local-ai','POST',{channel_id:$('#seo-channel').value,content_type:$('#seo-type').value,topic:$('#seo-topic').value});$('#seo-results').innerHTML='<h3>🧠 KoboldCpp local</h3><div class="seo-section"><pre>'+esc(v.generated)+'</pre></div><p class="muted small">'+esc(v.warning)+'</p>';toast('Text generat local; verifică-l înainte de publicare')}catch(e){toast(e.message)}};
$('#make-batch').onclick=async()=>{const ids=[...document.querySelectorAll('.item-select:checked')].map(x=>Number(x.value));if(!ids.length)return toast('Selectează măcar un material DRAFT');try{const b=await api('/batches','POST',{name:$('#batch-name').value,item_ids:ids});toast(`Lot #${b.id} trimis la aprobare`);await load();go('approvals')}catch(e){toast(e.message)}};
$('#spend-form').onsubmit=async e=>{e.preventDefault();const b={category:$('#spend-category').value,channel_id:$('#spend-channel').value||null,amount:Number($('#spend-amount').value),note:$('#spend-note').value};try{await api('/spend-proposals','POST',b);toast('Propunere salvată. Nu s-a făcut nicio plată.');$('#spend-note').value='';await load()}catch(err){toast(err.message)}};
$('#kill-toggle').onclick=async()=>{const next=!state.status.kill_switch;if(!next&&!confirm('Dezactivezi blocarea? Nicio publicare nu este posibilă în v1.'))return;try{await api('/settings/kill-switch','POST',{enabled:next});toast(next?'Kill Switch ACTIV':'Kill Switch dezactivat local. Publicarea rămâne indisponibilă.');await load()}catch(err){toast(err.message)}};
$('#csv-export').onclick=async()=>{try{const h={};if(key())h['X-BERRY-KEY']=key();const r=await fetch('/api/export.csv',{headers:h});if(!r.ok)throw Error('Export indisponibil');const blob=await r.blob(),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='berry_content.csv';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}catch(e){toast(e.message)}};
function renderStudioItems(){
 const sel=$('#studio-item');if(!sel)return;
 const old=sel.value;
 const drafts=state.items.filter(x=>x.status==='DRAFT');
 sel.innerHTML=drafts.length?drafts.map(x=>`<option value="${x.id}">#${x.id} · ${esc(names[x.channel_id])} · ${esc(types[x.content_type])} · ${esc(x.title)}</option>`).join(''):'<option value="">Creează un material DRAFT în Content Planner</option>';
 if([...sel.options].some(o=>o.value===old))sel.value=old;
}
async function refreshStudio(){
 try{
  const [caps,jobs]=await Promise.all([api('/studio/capabilities'),api('/studio/jobs')]);
  $('#studio-capabilities').innerHTML=Object.entries(caps.components).map(([id,c])=>`<div class="studio-component"><span>${c.ready?'🟢':'⚪'} <strong>${esc(id.replaceAll('_',' '))}</strong></span><small>${esc(c.detail)}</small></div>`).join('');
  $('#studio-jobs').innerHTML=jobs.length?jobs.map(j=>{
    const files=j.result?.files||[];
    const kinds=[['video','concept-preview.mp4','🎞 MP4'],['video','motion-video.mp4','🎞 MP4 FULL'],['script','script.txt','📝 Scenariu'],['subtitles','captions.srt','💬 SRT'],['image','character-concept.webp','🖼 Imagine'],['image','final-image.png','🖼 PNG final'],['soundtrack','soundtrack.mp3','🎵 Audio'],['soundtrack','soundtrack.wav','🎵 Audio'],['voice','voice.wav','🔊 Voce'],['manifest','manifest.json','📋 Manifest']];
    const links=kinds.filter(([kind,filename])=>files.includes(filename) || (kind==='soundtrack' && files.some(f=>f.includes('_soundtrack.')))).map(([kind,filename,label])=>`<button type="button" class="btn outline small" onclick="downloadStudio(${j.id},'${kind}','${filename}')">${label}</button>`).join(' ');
    return `<div class="studio-job"><div class="row-between"><strong>#${j.id} · ${esc(j.title)}</strong><span class="pill neutral">${esc(j.status)}</span></div><small>${esc(j.channel_id)} · ${esc(j.mode)} · ${esc(j.created_at)}</small><p class="muted small">${esc(j.error||j.result?.status_note||'Randare în curs...')}</p><div class="studio-links">${links}</div></div>`;
  }).join(''):'<div class="empty">Nu există randări. Selectează un material DRAFT și apasă Generează local.</div>';
 }catch(e){toast(e.message)}
}
window.downloadStudio=async(id,kind,filename)=>{
 try{
  const headers={};if(key())headers['X-BERRY-KEY']=key();
  const r=await fetch(`/api/studio/jobs/${id}/file/${kind}`,{headers});
  if(!r.ok)throw new Error(`Descărcare indisponibilă (${r.status})`);
  const blob=await r.blob(),url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),3000);
 }catch(e){toast(e.message)}
};
$('#studio-form').onsubmit=async e=>{
 e.preventDefault();const item_id=Number($('#studio-item').value);if(!item_id)return toast('Creează întâi un material DRAFT');
 try{const r=await api('/studio/render','POST',{item_id,mode:$('#studio-mode').value});toast(`Randare locală #${r.job_id} pornită`);await refreshStudio()}catch(err){toast(err.message)}
};
$('#studio-refresh').onclick=refreshStudio;
const originalGo=go;
go=function(page){originalGo(page);if(page==='studio')refreshStudio()};window.go=go;
// ---- BERRY 1.0 RC: QA, calendar, safe exports and user-supplied assets ----
function renderWorkflowSelectors(){
 for(const [selector, filter] of [['#qa-item',x=>true],['#calendar-item',x=>x.status==='APPROVED_NOT_PUBLISHED']]){
  const el=$(selector);if(!el)continue;const previous=el.value;
  el.innerHTML=state.items.filter(filter).map(x=>`<option value="${x.id}">#${x.id} · ${esc(names[x.channel_id])} · ${esc(x.title)}</option>`).join('')||'<option value="">Nu există materiale eligibile</option>';
  if([...el.options].some(o=>o.value===previous))el.value=previous;
 }
}
async function refreshQA(){
 const id=Number($('#qa-item').value);if(!id)return;
 try{
  const {review,report}=await api(`/qa/${id}`);
  for(const [field,id] of [['facts_checked','#qa-facts'],['visual_rights','#qa-visual'],['voice_rights','#qa-voice'],['music_rights','#qa-music'],['disclosure_checked','#qa-disclosure']])$(id).checked=Boolean(review[field]);
  $('#qa-notes').value=review.notes||'';
  showQA(report);
 }catch(e){toast(e.message)}
}
function showQA(r){
 $('#qa-results').innerHTML=`<div class="studio-job"><strong>${r.passed?'🟢 QA PASSED':'🟠 QA INCOMPLET'}</strong><p class="muted small">Material #${r.item_id} · randare #${r.job_id||'—'}</p><h4>Blocaje</h4>${r.reasons.length?r.reasons.map(x=>`<div class="qa-line">⛔ ${esc(x)}</div>`).join(''):'<p>Nu există blocaje automate.</p>'}<h4>Atenționări</h4>${r.warnings.length?r.warnings.map(x=>`<div class="qa-line">⚠️ ${esc(x)}</div>`).join(''):'<p>Nu există avertizări.</p>'}<p class="muted small">Acest QA nu certifică legal drepturile și nu publică nimic.</p></div>`;
}
$('#qa-item').onchange=refreshQA;
$('#qa-form').onsubmit=async e=>{
 e.preventDefault();const id=Number($('#qa-item').value);if(!id)return toast('Alege un material');
 const b={facts_checked:$('#qa-facts').checked,visual_rights:$('#qa-visual').checked,voice_rights:$('#qa-voice').checked,music_rights:$('#qa-music').checked,disclosure_checked:$('#qa-disclosure').checked,notes:$('#qa-notes').value};
 try{await api(`/qa/${id}/checks`,'POST',b);toast('Verificările au fost salvate');await refreshQA()}catch(e){toast(e.message)}
};
$('#qa-run').onclick=async()=>{const id=Number($('#qa-item').value);if(!id)return toast('Alege un material');try{const r=await api(`/qa/${id}/run`,'POST');showQA(r);toast(r.passed?'QA trecut':'QA incomplet; vezi blocajele')}catch(e){toast(e.message)}};
async function fetchDownload(path,filename){
 const headers={};if(key())headers['X-BERRY-KEY']=key();
 const r=await fetch('/api'+path,{headers});if(!r.ok){let j;try{j=await r.json()}catch{}throw Error(j?.detail||`HTTP ${r.status}`)}
 const url=URL.createObjectURL(await r.blob()),a=document.createElement('a');a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),5000);
}
async function refreshCalendar(){
 try{const rows=await api('/calendar');$('#calendar-list').innerHTML=rows.length?rows.map(x=>`<div class="studio-job"><div class="row-between"><strong>${esc(x.title)}</strong><span class="pill neutral">${esc(x.status)}</span></div><p class="muted small">${esc(x.platform)} · ${esc(new Date(x.scheduled_at).toLocaleString('ro-RO'))} · #${x.item_id}</p>${x.qa_still_valid===false?'<p>⚠️ QA a fost modificat. Revalidare necesară.</p>':''}<div class="buttons">${x.status!=='CANCELLED'?`<button class="btn outline small" onclick="downloadSchedule(${x.id})">↓ Pachet ZIP</button>`:''}${x.status==='SCHEDULED_LOCAL'?`<button class="btn outline small" onclick="cancelSchedule(${x.id})">Anulează</button>`:''}</div></div>`).join(''):'<div class="empty">Nicio programare. Mai întâi: FULL render → QA → aprobare umană.</div>'}catch(e){toast(e.message)}
}
window.downloadSchedule=async id=>{try{await fetchDownload(`/calendar/${id}/package`,`BERRY_PUBLICATION_${id}.zip`);toast('Pachet local descărcat, NU publicat');await refreshCalendar()}catch(e){toast(e.message)}};
window.cancelSchedule=async id=>{if(!confirm('Anulezi programarea locală?'))return;try{await api(`/calendar/${id}/cancel`,'POST');await refreshCalendar();toast('Programare anulată')}catch(e){toast(e.message)}};
$('#calendar-form').onsubmit=async e=>{e.preventDefault();const item_id=Number($('#calendar-item').value),v=$('#calendar-time').value;if(!item_id||!v)return toast('Selectează un material aprobat și o dată');
 try{await api('/calendar','POST',{item_id,platform:$('#calendar-platform').value,scheduled_at:new Date(v).toISOString()});toast('Programat local. Nu se publică automat.');await refreshCalendar()}catch(e){toast(e.message)}};
$('#calendar-refresh').onclick=refreshCalendar;
$('#backup-download').onclick=async()=>{try{await fetchDownload('/backup','BERRY_BACKUP.zip');toast('Backup descărcat; păstrează-l privat')}catch(e){toast(e.message)}};
async function uploadAsset(inputId,endpoint){const item_id=Number($('#studio-item').value),file=$(inputId).files[0];if(!item_id||!file)return toast('Selectează un material și un fișier');const form=new FormData();form.append('file',file);
 const headers={};if(key())headers['X-BERRY-KEY']=key();
 try{const r=await fetch(`/api/items/${item_id}/${endpoint}`,{method:'POST',headers,body:form});const j=await r.json();if(!r.ok)throw Error(j.detail||'Import eșuat');toast(`Fișier salvat local: ${j.filename}. Randează din nou FULL.`);$(inputId).value='';await refreshStudio()}catch(e){toast(e.message)}
}
$('#upload-art').onclick=()=>uploadAsset('#studio-art','art');
$('#upload-audio').onclick=()=>uploadAsset('#studio-audio','soundtrack');
async function loadScript(){const id=Number($('#studio-item').value);if(!id){$('#studio-script').value='';return}try{const r=await api(`/items/${id}/script`);$('#studio-script').value=r.text;$('#studio-script').disabled=!r.editable;$('#studio-script-save').disabled=!r.editable}catch(e){toast(e.message)}}
$('#studio-item').onchange=loadScript;
$('#studio-script-save').onclick=async()=>{const id=Number($('#studio-item').value);if(!id)return toast('Alege un material');try{await api(`/items/${id}/script`,'POST',{text:$('#studio-script').value});toast('Scenariu salvat. Randează din nou FULL.');await refreshStudio()}catch(e){toast(e.message)}};
$('#studio-next').onclick=async()=>{try{const r=await api('/studio/render-next','POST');toast(r.job_id?`Randare FULL #${r.job_id} pornită`:'Nu există schițe de randat');await refreshStudio()}catch(e){toast(e.message)}};
async function refreshProduction(){try{const runs=await api('/production/runs');$('#production-runs').innerHTML=runs.length?runs.map(r=>`<div class="studio-job"><div class="row-between"><strong>Lot #${r.id} · ${esc(r.status)}</strong><span>${r.completed}/${r.total} · eșuate: ${r.failed}</span></div>${['RUNNING','QUEUED'].includes(r.status)?`<button class="btn outline small" onclick="cancelProduction(${r.id})">Oprește după randarea curentă</button>`:''}</div>`).join(''):'<div class="empty">Nu există loturi de producție.</div>'}catch(e){toast(e.message)}}
window.cancelProduction=async id=>{try{await api(`/production/${id}/cancel`,'POST');toast('Oprire solicitată');await refreshProduction()}catch(e){toast(e.message)}};
$('#production-start').onclick=async()=>{if(!confirm('Pornim randarea FULL pentru maximum 30 schițe locale? Poate dura mult pe CPU.'))return;try{const r=await api('/production/start','POST');toast(`Lot #${r.run_id} pornit pentru ${r.total} fișe`);await refreshProduction()}catch(e){toast(e.message)}};
const priorGo=go;go=function(page){priorGo(page);if(page==='qa')refreshQA();if(page==='calendar')refreshCalendar();if(page==='studio'){loadScript();refreshProduction()}};window.go=go;
load();
if('serviceWorker'  in navigator)navigator.serviceWorker.register('/static/sw.js').catch(()=>{});

// ---- BERRY 1.1 RC: opt-in local AI and offline analytics ----
async function refreshAI(){
 try{
  const r=await api('/engines');
  $('#ai-engines').innerHTML=Object.entries(r.engines).map(([name,v])=>`<div class="studio-component"><div class="row-between"><strong>${esc(name)}</strong><span class="pill neutral">${v.ready?'READY':v.online?'ONLINE · CONFIG':'NECONFIGURAT'}</span></div><small>${esc(v.detail)}</small></div>`).join('');
  const jobs=await api('/ai/jobs');
  $('#ai-jobs').innerHTML=jobs.length?jobs.map(j=>`<div class="studio-job"><strong>#${j.id} · ${esc(j.engine)} · ${esc(j.status)}</strong><p class="muted small">${esc(j.title)} · ${esc(j.error||((j.result?.filename||'În așteptare')+(j.result?.elapsed_seconds!==undefined?' · '+j.result.elapsed_seconds+' sec':'') ))}</p></div>`).join(''):'<div class="empty">Nu există generări AI locale.</div>';
  const selected=$('#ai-item').value;
  $('#ai-item').innerHTML=state.items.filter(i=>i.status==='DRAFT').map(i=>`<option value="${i.id}">#${i.id} · ${esc(i.title)}</option>`).join('')||'<option value="">Creează un material DRAFT</option>';
  if([...$('#ai-item').options].some(o=>o.value===selected))$('#ai-item').value=selected;
 }catch(e){toast(e.message)}
}
$('#ai-refresh').onclick=refreshAI;
$('#ai-form').onsubmit=async e=>{
 e.preventDefault();const id=Number($('#ai-item').value);if(!id)return toast('Creează un material DRAFT');
 const engine=$('#ai-engine').value;
 if(!confirm(`Pornești ${engine} pe PC-ul local? Poate consuma multă memorie și timp.`))return;
 try{const r=await api('/ai/jobs','POST',{item_id:id,engine});toast(`Job AI #${r.job_id} pornit local`);await refreshAI()}catch(err){toast(err.message)}
};
async function refreshAnalytics(){
 try{const r=await api('/analytics');
 $('#analytics-channels').innerHTML=r.channels.length?r.channels.map(x=>`<div class="studio-job"><div class="row-between"><strong>${esc(names[x.channel_id]||x.channel_id)}</strong><span>${Number(x.views).toLocaleString('ro-RO')} vizualizări</span></div><p class="muted small">${x.posts} postări · ${x.engagement_percent}% interacțiuni/vizualizări</p></div>`).join(''):'<div class="empty">Nu ai importat încă statistici CSV.</div>';
 $('#analytics-suggestions').innerHTML=r.suggestions.length?r.suggestions.map(x=>`<div class="qa-line">💡 ${esc(x)}</div>`).join(''):'<div class="empty">Recomandările apar după import.</div>';
 }catch(e){toast(e.message)}
}
$('#analytics-refresh').onclick=refreshAnalytics;
$('#analytics-upload').onclick=async()=>{
 const file=$('#analytics-file').files[0];if(!file)return toast('Selectează un CSV');
 const form=new FormData();form.append('file',file);const headers={};if(key())headers['X-BERRY-KEY']=key();
 try{const r=await fetch('/api/analytics/import',{method:'POST',headers,body:form});const data=await r.json();if(!r.ok)throw Error(data.detail||'Import eșuat');toast(`${data.imported} rânduri importate, ${data.duplicates} duplicate`);await refreshAnalytics()}catch(e){toast(e.message)}
};
$('#upload-voice').onclick=()=>uploadAsset('#studio-voice','voice');
$('#upload-video').onclick=()=>uploadAsset('#studio-video','video');
const priorGoAI=go;go=function(page){priorGoAI(page);if(page==='ai-local')refreshAI();if(page==='analytics')refreshAnalytics()};window.go=go;

// Diagnostic only: no AI generation, downloads or network requests outside localhost.
if(document.querySelector("#local-diagnostics")){document.querySelector("#local-diagnostics").onclick=async()=>{const out=document.querySelector("#local-diagnostics-report");out.textContent="Se verifică sistemul local...";try{const response=await fetch("/api/local/diagnostics");if(!response.ok)throw Error("HTTP "+response.status);out.textContent=JSON.stringify(await response.json(),null,2)}catch(e){out.textContent="Diagnostic indisponibil: "+String(e.message)}};}


// YouTube Google OAuth: local planning only. No Google redirect or token exchange.
let youtubePlan=null;
async function refreshYoutubePlan(){
 const status=$('#youtube-oauth-status'),list=$('#youtube-oauth-channels');
 if(!status||!list)return;
 try{
  const data=await api('/integrations/youtube/plan');youtubePlan=data;
  status.textContent='Stare: '+data.mode+' · '+data.planned_count+'/5 asocieri planificate · '+data.connected_count+'/5 conectate · client Google configurat: '+(data.client_id_staged?'da':'nu')+' · fișier secret configurat: '+(data.client_secret_file_staged?'da':'nu')+' · publicare: DEZACTIVATĂ';
  list.innerHTML=data.channels.map(ch=>'<div class="item-row"><div class="item-main"><strong>'+esc(ch.fruit_name)+'</strong><small>'+esc(ch.display_label||'Nume YouTube necompletat')+' · '+esc(ch.youtube_channel_id||'ID YouTube necompletat')+'</small><small>'+(ch.planned?'Asociere locală, neverificată':'Neplanificat')+' · OAuth neconectat</small></div>'+(ch.planned?'<button class="btn small outline youtube-plan-remove" data-fruit="'+esc(ch.fruit_channel_id)+'" type="button">Șterge planul</button>':'')+'</div>').join('');
  const selected=data.channels.find(x=>x.fruit_channel_id===$('#youtube-plan-fruit').value);
  if(selected){$('#youtube-plan-label').value=selected.display_label||'';$('#youtube-plan-id').value=selected.youtube_channel_id||'';}
 }catch(e){status.textContent='Nu am putut încărca planul YouTube: '+e.message;}
}
$('#youtube-plan-refresh').onclick=refreshYoutubePlan;
$('#youtube-plan-fruit').onchange=()=>{
 const selected=youtubePlan?.channels?.find(x=>x.fruit_channel_id===$('#youtube-plan-fruit').value);
 $('#youtube-plan-label').value=selected?.display_label||'';
 $('#youtube-plan-id').value=selected?.youtube_channel_id||'';
};
$('#youtube-plan-form').onsubmit=async e=>{
 e.preventDefault();
 const body={fruit_channel_id:$('#youtube-plan-fruit').value,
             display_label:$('#youtube-plan-label').value.trim(),
             youtube_channel_id:$('#youtube-plan-id').value.trim()||null};
 try{await api('/integrations/youtube/channel-plan','POST',body);toast('Asociere locală salvată. Canalul NU este conectat.');await refreshYoutubePlan();}catch(err){toast(err.message)}
};
$('#youtube-oauth-channels').addEventListener('click',async e=>{
 const btn=e.target.closest('.youtube-plan-remove');if(!btn)return;
 if(!confirm('Ștergi doar asocierea locală, fără modificări în YouTube?'))return;
 try{await api('/integrations/youtube/channel-plan/'+encodeURIComponent(btn.dataset.fruit),'DELETE');toast('Plan local șters');await refreshYoutubePlan();}catch(err){toast(err.message)}
});
const priorGoYoutube=go;
go=function(page){priorGoYoutube(page);if(page==='integrations')refreshYoutubePlan()};window.go=go;


// Explicit local Instagram Agent Skill analysis. No social login or publishing.
const igToolsForm=$('#ig-tools-form');
if(igToolsForm){
 igToolsForm.addEventListener('submit',async event=>{
  event.preventDefault();
  const result=$('#ig-tools-result');
  const kind=$('#ig-tools-kind').value;
  const text=$('#ig-tools-text').value.trim();
  const max=kind==='hook'?240:kind==='caption'?2200:5000;
  if(!text||text.length>max){result.textContent='Textul trebuie să aibă între 1 și '+max+' caractere.';return;}
  result.textContent='Verificare locală în curs...';
  try{
   const answer=await api('/seo/instagram/analyze','POST',{
    kind,text,target_seconds:Number($('#ig-tools-target').value||15),keywords:''
   });
   result.textContent=JSON.stringify(answer.result,null,2)+'\n\n'+answer.language_note+
    '\nFără conectare Instagram · fără publicare · verificare umană obligatorie.';
  }catch(err){result.textContent='Instrument indisponibil: '+err.message;}
 });
}


// HyperFrames CLI: user-triggered local render of a BERRY-generated composition.
async function refreshHyperFrames(){
 const status=$('#hf-status'),jobs=$('#hf-jobs');
 if(!status||!jobs)return;
 try{
  const [cap,list]=await Promise.all([api('/studio/hyperframes/status'),api('/studio/hyperframes/jobs')]);
  status.textContent=cap.cli_configured?'CLI configurat · render local':'CLI indisponibil · configurează BERRY_HYPERFRAMES_BIN';
  jobs.replaceChildren();
  if(!list.length){jobs.textContent='Nu există randări HyperFrames.';return;}
  for(const job of list){
   const row=document.createElement('div');row.className='item-row';
   const info=document.createElement('div');info.className='item-main';
   info.textContent='Job #'+job.id+' · Material #'+job.item_id+' · '+job.status+
    ' · '+job.duration_seconds+'s'+(job.error?' · '+job.error:'');
   row.append(info);
   if(job.video_ready){
    const btn=document.createElement('button');btn.className='btn small outline';
    btn.textContent='Descarcă MP4';
    btn.onclick=async()=>{
     try{
      const resp=await fetch('/api/studio/hyperframes/jobs/'+job.id+'/video',
       {headers:key()?{'X-BERRY-KEY':key()}:{}});
      if(!resp.ok)throw Error('HTTP '+resp.status);
      const blob=await resp.blob(),url=URL.createObjectURL(blob);
      const a=document.createElement('a');a.href=url;a.download='berry-hyperframes-'+job.id+'.mp4';
      a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);
     }catch(err){toast('Descărcarea a eșuat: '+err.message);}
    };
    row.append(btn);
   }
   jobs.append(row);
  }
 }catch(err){status.textContent='HyperFrames: '+err.message;}
}
if($('#hf-refresh'))$('#hf-refresh').onclick=refreshHyperFrames;
if($('#hf-render'))$('#hf-render').onclick=async()=>{
 const id=Number($('#studio-item')?.value);
 if(!id){toast('Selectează întâi un material DRAFT în Media Studio.');return;}
 if(!confirm('Randezi local un MP4-concept pentru acest material? Nu este animație AI 3D și nu se publică.'))return;
 try{
  const result=await api('/studio/hyperframes/render','POST',{item_id:id});
  toast('HyperFrames: job #'+result.id+' adăugat.');
  await refreshHyperFrames();
 }catch(err){toast('HyperFrames: '+err.message);}
};
const previousGoHF=go;
go=function(page){previousGoHF(page);if(page==='studio')refreshHyperFrames()};window.go=go;

// Optional social OAuth, explicitly activated by the user; only profile/read scopes.
async function refreshSocialAccounts(){
 const target=$('#social-status');
 if(!target)return;
 target.replaceChildren();
 try{
  const data=await api('/social/status');
  const note=document.createElement('p');note.className='muted small';
  note.textContent='OAuth: '+(data.enabled?'ACTIVAT EXPLICIT':'DEZACTIVAT')+
    ' · publicare: DEZACTIVATĂ · permisiuni de upload: NU';
  target.append(note);
  for(const [name,provider] of Object.entries(data.providers)){
   const indicator=$('#integration-'+name);
   if(indicator)indicator.textContent=provider.connected.length?
    provider.connected.length+' CONTURI CONECTATE · DOAR CITIRE':'NECONECTAT';
   const row=document.createElement('div');row.className='item-row';
   const info=document.createElement('div');info.className='item-main';
   info.textContent=name.toUpperCase()+' · '+(provider.configured?'chei configurate':'chei lipsă')+
    ' · '+(provider.redirect_ready?'callback pregătit':'callback HTTPS necesar')+
    ' · conturi: '+provider.connected.length;
   row.append(info);target.append(row);
   for(const account of provider.connected){
    const entry=document.createElement('div');entry.className='item-row';
    const label=document.createElement('div');label.className='item-main';
    label.textContent='Conectat: '+account.display_name+' · '+account.channel_id+' · doar citire';
    const disconnect=document.createElement('button');disconnect.type='button';
    disconnect.className='btn small outline';disconnect.textContent='Deconectează local';
    disconnect.onclick=async()=>{
     if(!confirm('Ștergi tokenul local? Revocă separat accesul și din contul platformei.'))return;
     try{await api('/social/'+name+'/disconnect','POST',{channel_id:account.channel_id});
      await refreshSocialAccounts();toast('Token local șters.');
     }catch(err){toast(err.message);}
    };
    entry.append(label,disconnect);
    if(name==='youtube'){
     const stats=document.createElement('button');stats.type='button';
     stats.className='btn small outline';stats.textContent='Statistici YouTube';
     stats.onclick=async()=>{
      const result=$('#social-link-result');
      result.textContent='Se citesc statisticile canalului...';
      try{
       const data=await api('/social/youtube/channel-stats','POST',{channel_id:account.channel_id});
       result.textContent='YouTube · '+data.display_name+' · vizualizări totale: '+
        data.views_total+' · videoclipuri: '+data.videos_total+
        ' · abonați: '+(data.subscribers??'ascunși')+
        ' · doar citire, fără publicare.';
      }catch(err){result.textContent='Statistici indisponibile: '+err.message;}
     };
     entry.append(stats);
    }
    target.append(entry);
   }
  }
 }catch(err){target.textContent='Conectare opțională indisponibilă: '+err.message;}
}
if($('#social-refresh'))$('#social-refresh').onclick=refreshSocialAccounts;
if($('#social-link-form'))$('#social-link-form').onsubmit=async event=>{
 event.preventDefault();
 const target=$('#social-link-result');target.replaceChildren();
 const provider=$('#social-provider').value,channel_id=$('#social-channel').value;
 if(!confirm('Vrei să pregătești autentificarea oficială '+provider+' pentru '+channel_id+
             '? Doar citire, fără publicare.'))return;
 try{
  const response=await api('/social/'+provider+'/start','POST',{channel_id});
  const p=document.createElement('p');
  p.textContent='Link valabil 10 minute. Verifică platforma și permisiunile înainte de acord.';
  const link=document.createElement('a');link.href=response.authorization_url;
  link.target='_blank';link.rel='noopener noreferrer';link.textContent='Deschide autentificarea oficială '+provider;
  target.append(p,link);
 }catch(err){target.textContent='Nu se poate conecta: '+err.message;}
};
const previousGoSocial=go;
go=function(page){previousGoSocial(page);if(page==='integrations')refreshSocialAccounts()};window.go=go;
if(new URLSearchParams(location.search).has('oauth')){
 const value=new URLSearchParams(location.search).get('oauth');
 toast(value==='connected'?'Cont conectat pentru citire. Verifică starea în Integrări.':
       'OAuth nu s-a finalizat. Verifică setările și reîncearcă.');
 history.replaceState({},'',location.pathname);
}
