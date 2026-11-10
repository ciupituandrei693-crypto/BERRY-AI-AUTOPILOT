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
function go(page){if(!$('#page-'+page))return;state.view=page;document.querySelectorAll('.page').forEach(x=>x.classList.toggle('active',x.id==='page-'+page));document.querySelectorAll('.nav-btn').forEach(x=>x.classList.toggle('active',x.dataset.page===page));$('#view-title').textContent=({overview:'Prezentare generală',channels:'Biblioteca de personaje',planner:'Content Planner',seo:'SEO Studio',approvals:'Approval Center',budgets:'Budget Guard',integrations:'Integrări & securitate',studio:'Media Studio'})[page];window.scrollTo({top:0,behavior:'smooth'})}
window.go=go;
async function load(){try{const [status,channels,characters,items,batches,budget,audit]=await Promise.all([api('/status'),api('/channels'),api('/characters'),api('/items'),api('/batches'),api('/budget'),api('/audit')]);Object.assign(state,{status,channels,characters,items,batches,budget,audit});render()}catch(e){toast(e.message)}}
function opts(){for(const id of ['#new-channel','#seo-channel','#filter-channel','#spend-channel']){const sel=$(id),old=sel.value,empty=id.includes('filter')?'<option value="">Toate canalele</option>':id.includes('spend')?'<option value="">Niciun canal (pentru GPU/general)</option>':'';sel.innerHTML=empty+state.channels.map(c=>`<option value="${esc(c.id)}">${esc(c.name)}</option>`).join('');if([...sel.options].some(o=>o.value===old))sel.value=old}}
function render(){opts();$('#metric-channels').textContent=state.status.channels;$('#metric-items').textContent=state.status.items;$('#metric-batches').textContent=state.status.pending_batches;$('#kill-overview').textContent=state.status.kill_switch?'Activ':'Inactiv';$('#kill-overview').style.color=state.status.kill_switch?'#62dbb4':'#efa5af';$('#mode-pill').textContent=state.status.mode.replaceAll('_',' ');$('#kill-toggle').textContent=state.status.kill_switch?'Dezactivează comutatorul':'ACTIVEAZĂ KILL SWITCH';renderChannels();renderItems();renderBatches();renderBudget();renderAudit();renderStudioItems()}
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
    const kinds=[['video','concept-preview.mp4','🎞 MP4'],['script','script.txt','📝 Scenariu'],['subtitles','captions.srt','💬 SRT'],['image','character-concept.webp','🖼 Imagine'],['voice','voice.wav','🔊 Voce'],['manifest','manifest.json','📋 Manifest']];
    const links=kinds.filter(([kind,filename])=>files.includes(filename)).map(([kind,filename,label])=>`<button type="button" class="btn outline small" onclick="downloadStudio(${j.id},'${kind}','${filename}')">${label}</button>`).join(' ');
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
load();
if('serviceWorker'  in navigator)navigator.serviceWorker.register('/static/sw.js').catch(()=>{});
