/* EMBERLINE. Vanilla JS with zero client-side dependencies. All processing uses the FastAPI ML service. */
'use strict';
const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const h = value => String(value??'').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let store={cases:[],events:[],volunteers:[],stock:{},inbox:[],metrics:{}};
let filter='ALL',screen='overview',activeCase=null;
const originalStock={kits:3,litres:30,meals:12,seats:5,beds:3};
const glyph={Medical:'✚',Water:'◉',Food:'◈',Transport:'➜',Shelter:'⌂',Other:'◎'};
const toast = msg => {const t=$('#toast');t.textContent=msg;t.classList.remove('hidden');clearTimeout(toast.timer);toast.timer=setTimeout(()=>t.classList.add('hidden'),3200)};
async function api(path,method='GET',body=null){
 const opts={method,headers:{'Content-Type':'application/json'}};
 if(body!==null)opts.body=JSON.stringify(body);
 const r=await fetch('/api/'+path,opts);let o=await r.json();
 if(!r.ok)throw Error(typeof o.detail==='string'?o.detail:'Request failed');return o;
}
const xpriority=p=>p==='CRITICAL'?'critical':p==='HIGH'?'high':'normal';
const priorityChip=p=>`<span class="chip ${xpriority(p)}">${h(p)}</span>`;
const statusChip=s=>`<span class="chip ${s==='APPROVED'?'approved':s==='DUPLICATE'?'duplicate':'status'}">${h(s)}</span>`;
function metric(id,value){const el=$('#'+id);if(el)el.textContent=value}
function render(){
 const m=store.metrics||{};metric('mProcessed',m.processed??0);metric('mMatched',m.matched??0);metric('mDuplicates',m.duplicates??0);metric('mCritical',m.critical??0);
 $('#mProcessed').insertAdjacentHTML('beforeend',`<span class="dim"> ${store.inbox?.length?' / 11 sample':''}</span>`);
 $('#queueCount').textContent=`${m.open||0} OPEN · ${m.matched||0} MATCHED`;
 $('#runLabel').textContent=store.inbox?.length?`Process ${store.inbox.length} inbox messages`:'Inbox processed';$('#runDemo').disabled=!store.inbox?.length;
 renderQueue();renderRequests();renderResources();renderAudit();renderOptimization();
 if(activeCase){const c=store.cases.find(x=>x.id===activeCase);if(c)renderDetails(c)}
}
function renderQueue(){
 const c=[...store.cases].filter(x=>['OPEN','MATCHED','REVIEW','CRITICAL','REJECTED'].includes(x.status)||x.emergency_flag).sort((a,b)=>(Number(b.emergency_flag)-Number(a.emergency_flag))||({CRITICAL:0,HIGH:1,NORMAL:2}[a.priority]-{CRITICAL:0,HIGH:1,NORMAL:2}[b.priority])||a.id.localeCompare(b.id));
 if(!c.length){$('#actionQueue').innerHTML='<div class="empty"><span>⌑</span><b>Waiting for signals</b><small>Process the sample inbox to generate actionable cases.</small></div>';return}
 $('#actionQueue').innerHTML=c.slice(0,10).map(v=>`<div class="action-card" data-case="${h(v.id)}" tabindex="0" role="button" aria-label="Open case ${h(v.id)}"><div class="action-symbol">${glyph[v.category]}</div><div class="action-main"><div class="action-top">${h(v.id)} · ${h(v.category)} <span>↗</span></div><p>${h(v.message)}</p><div class="action-meta">${priorityChip(v.priority)} <span class="chip">${h(v.zone)}</span> ${statusChip(v.status)}</div></div></div>`).join('');
 $$('.action-card').forEach(card=>{card.addEventListener('click',()=>openCase(card.dataset.case));card.addEventListener('keydown',e=>{if(e.key==='Enter')openCase(card.dataset.case)})});
}
function renderRequests(){
 const rows=store.cases.filter(c=>filter==='ALL'||c.status===filter);
 $('#requestRows').innerHTML=rows.length?rows.map(c=>`<tr><td><b>${h(c.id)}</b></td><td class="signal">${h(c.message)}</td><td>${h(c.category)}<span class="conf">ML confidence ${Math.round(c.confidence*100)}% · ${h(c.resource)} × ${c.demand}</span></td><td>${h(c.zone)}</td><td>${priorityChip(c.priority)}</td><td>${statusChip(c.status)}</td><td><button class="more" data-case="${h(c.id)}">Inspect →</button></td></tr>`).join(''):'<tr><td colspan="7" style="text-align:center;padding:75px;color:#748aa1">No cases in this view. Process the inbox to begin.</td></tr>';
 $$('#requestRows .more').forEach(btn=>btn.addEventListener('click',()=>openCase(btn.dataset.case)));
}
function renderResources(){
 const labels=[['kits','Medical kits','✚'],['litres','Drinking water','◉'],['meals','Meal portions','◈'],['seats','Transport seats','➜'],['beds','Shelter beds','⌂']];
 $('#inventoryGrid').innerHTML=labels.map(([key,name,icon])=>{const val=store.stock?.[key]??0;const pct=Math.round(val/originalStock[key]*100);return `<div class="inventory-card"><div class="inventory-icon">${icon}</div><h3>${name}</h3><strong>${val}</strong><small>available · initial ${originalStock[key]}</small><div class="capacity-bar"><span style="width:${pct}%"></span></div></div>`}).join('');
 $('#volunteerGrid').innerHTML=(store.volunteers||[]).map(v=>`<div class="volunteer-card"><div class="volunteer-card-top"><span class="person-avatar">${h(v.name.slice(0,2).toUpperCase())}</span><div><b>${h(v.name)}</b><small>${h(v.zone)} · ${h(v.id)}</small></div></div><div class="skills">${v.skills.map(sk=>`<span class="chip">${h(sk)}</span>`).join('')}</div><div class="volunteer-card-foot"><span>Remaining capacity</span><b>${v.available} assignments</b></div></div>`).join('');
}
function renderAudit(){
 $('#auditRows').innerHTML=store.events?.length?store.events.map(e=>`<div class="audit-row"><span class="audit-icon">${{classify:'✳',match:'⌘',approval:'✓',safety:'!',dedupe:'◫',optimizer:'✦',system:'↻',batch:'↧',review:'◉',reject:'✕',override:'↩',reopen:'↺'}[e.kind]||'◎'}</span><div class="audit-text"><b>${h(e.kind)}</b>${h(e.message)}</div><time>${h(e.at)}</time></div>`).join(''):'<div class="empty"><span>≡</span><b>No events yet</b><small>Every workflow action will leave an audit trail here.</small></div>';
}
function renderOptimization(){
 const o=store.optimizer||{};
 const box=$('#optimizerDiagnostics');if(!box)return;
 const solvable=o.optimal===true?'OPTIMAL SOLUTION CERTIFIED':o.optimal===false?'FEASIBLE SOLUTION · optimality unverified':'AWAITING OPTIMIZATION';
 box.innerHTML=`<div class="optimizer-header"><div><div class="small-eyebrow">INTELLIGENCE / OPERATIONS RESEARCH</div><h3>Proof, not guesswork.</h3></div><span class="chip approved">${solvable}</span></div>
 <p>0–1 integer programming jointly allocates volunteers and supplies. A candidate assignment exists only if the required skill, available volunteer slot and adequate global inventory are present. Final stock is consumed <b>only after human approval.</b></p>
 <div class="optimizer-kpis"><div><small>FEASIBLE PROPOSALS</small><strong>${Number(o.selected||0)}</strong></div><div><small>OBJECTIVE SCORE</small><strong>${Number(o.objective||0).toFixed(1)}</strong></div><div><small>CANDIDATE PAIRS</small><strong>${Number(o.candidate_pairs||0)}</strong></div><div><small>SOLVER TIME</small><strong>${Number(o.solve_ms||0).toFixed(1)} ms</strong></div></div>
 <p class="small-note">Optimization is exact for this <em>simplified synthetic model</em>, not a promise of the best real-world emergency outcome. Classifier probabilities are uncalibrated and no physical routing, responder validation or real dispatch occurs.</p>`;
}
function renderScenario(r){
 const el=$('#scenarioResults'); if(!el)return;
 const impact=r.impact;
 const label=(n)=> n>0?'+'+n:String(n);
 el.innerHTML=`<div class="lab-comparison"><div class="lab-before"><small>01 · CURRENT FEASIBLE PLAN</small><strong>${r.baseline.selected}</strong><span>requests covered</span><b>Utility ${Number(r.baseline.objective).toFixed(1)}</b></div><div class="lab-vs">→</div><div class="lab-after"><small>02 · COUNTERFACTUAL PLAN</small><strong>${r.counterfactual.selected}</strong><span>requests covered</span><b>Utility ${Number(r.counterfactual.objective).toFixed(1)}</b></div></div><div class="lab-impact"><span>Coverage change <b>${label(impact.delta_coverage)}</b></span><span>Utility change <b>${label(impact.delta_utility)}</b></span><span>Reassigned <b>${impact.reassigned.length}</b></span></div><div class="lab-cases">${impact.lost_coverage.length?`<div class="lab-loss">Lost coverage: <b>${impact.lost_coverage.map(h).join(', ')}</b></div>`:''}${impact.gained_coverage.length?`<div class="lab-gain">Newly covered: <b>${impact.gained_coverage.map(h).join(', ')}</b></div>`:''}${impact.reassigned.length?`<div>Different volunteer: <b>${impact.reassigned.map(h).join(', ')}</b></div>`:''}${!impact.lost_coverage.length&&!impact.gained_coverage.length&&!impact.reassigned.length?'<div class="lab-gain">Plan resilient to this simulated change; no case changed coverage or volunteer.</div>':''}</div><div class="lab-verification">${r.baseline.optimal&&r.counterfactual.optimal?'✓ Both simulated plans proven optimal for their constrained mathematical model.':'Feasible plans; optimality not certified for one or both models.'} No real-world effect was measured.</div>`;
}
async function runScenario(){
 const btn=$('#simulateBtn'), el=$('#scenarioResults');if(!btn||!el)return;
 btn.disabled=true; el.textContent='Re-solving mathematical model under synthetic disruption…';
 try{const r=await api('scenario','POST',{preset:$('#scenarioPreset').value});renderScenario(r)}
 catch(e){el.textContent='Could not complete scenario: '+e.message;toast('Scenario failed: '+e.message)}
 finally{btn.disabled=false}
}
function renderDetails(c){
 $('#dialogId').textContent=c.id+' · '+c.category;
 const v=store.volunteers.find(x=>x.id===c.assigned_volunteer);
 const alert=c.emergency_flag?'<div class="warning">⚑ Potential life-threatening emergency. This is NOT an emergency service. Contact local emergency services directly. Automated assignments are blocked.</div>':'';
 const duplicate=c.duplicate_of?`<div class="warning">Potential duplicate of ${h(c.duplicate_of)} · ${Math.round(c.duplicate_similarity*100)}% text similarity. This is a review suggestion, not confirmed identity.</div>`:'';
 let buttons='';
 if(c.status==='MATCHED')buttons=`<button class="primary-btn" id="approveCase">✓ Approve & reserve supplies</button><button class="ghost-btn" id="previewDraft">View NOT-SENT dispatch draft</button><button class="ghost-btn" id="rejectCase">Reject proposal</button>`;
 else if(c.status==='APPROVED')buttons='<button class="ghost-btn" id="previewDraft">View NOT-SENT approved draft</button>';
 else if(c.status==='OPEN'&&!c.emergency_flag)buttons='<button class="secondary-btn" id="matchThis">↗ Recompute optimal assignments</button>';
 else if(c.status==='REJECTED')buttons='<button class="secondary-btn" id="reopenCase">↺ Reopen for optimization</button>';
 else if(c.status==='DUPLICATE')buttons='<button class="secondary-btn" id="distinctCase">This is a distinct request — override duplicate</button>';
 else if(c.status==='CRITICAL')buttons='<button class="ghost-btn" id="escalateCase">I have read this safety warning · acknowledge</button><button class="secondary-btn" id="attestEscalation">I personally contacted emergency services · record attestation (DEMO)</button>';
 const canReview=!c.emergency_flag&&!c.duplicate_of&&!['APPROVED','ESCALATED','REJECTED'].includes(c.status);
 const cats=['Medical','Water','Food','Transport','Shelter','Other'];
 const zones=['Rhodes Town','Ialyssos','Kremasti','Faliraki','Archangelos','Lindos'];
 const reviewForm=canReview?`<details class="review-disclosure" ${c.status==='REVIEW'?'open':''}><summary>Human verification · edit extracted fields</summary><form id="reviewForm" class="review-form"><label>Category<select name="category">${cats.map(x=>`<option ${x===c.category?'selected':''}>${h(x)}</option>`).join('')}</select></label><label>Zone<select name="zone">${zones.map(x=>`<option ${x===c.zone?'selected':''}>${h(x)}</option>`).join('')}</select></label><label>Requested units<input name="demand" type="number" min="1" max="30" value="${Number(c.demand)}" required></label><button type="submit" class="secondary-btn">✓ Confirm corrected fields</button></form></details>`:'';
 const explanation=v?`<div class="detail-quote">${h(v.name)} · ${h(v.zone)}</div><ul class="rationale-list">${(c.match_explanation||[]).map(why=>`<li>${h(why)}</li>`).join('')}</ul><p class="detail-note">Utility score ${h(c.match_score)}. Proposal only; no dispatch message has been sent.</p>`:`<p class="detail-note">${h(c.unmatched_reason||'No assignment yet. Matching checks skills, capacity and inventory, and prioritizes cases in an exact optimization model.')}</p>`;
 $('#dialogContent').innerHTML=`<div class="detail-section"><div class="detail-label">ORIGINAL INPUT — PRESERVED FOR AUDIT</div><div class="detail-quote">“${h(c.message)}”</div></div><div class="detail-section"><div class="detail-label">AI EXTRACTION & UNCERTAINTY</div><div class="detail-metrics"><div><small>Predicted category</small><b>${h(c.category)}</b></div><div><small>Model probability*</small><b>${Math.round(c.confidence*100)}%</b></div><div><small>Priority</small>${priorityChip(c.priority)}</div><div><small>Detected zone</small><b>${h(c.zone)}</b></div><div><small>Required inventory</small><b>${c.demand} ${h(c.resource)}</b></div><div><small>Workflow status</small>${statusChip(c.status)}</div></div><p class="detail-note">*Uncalibrated model probability on synthetic training data — not a verified chance of correctness. Human verification required before any real use.</p>${c.needs_review?'<div class="warning">Human review required: insufficient certainty, absent location or safety flag.</div>':''}${alert}${duplicate}${reviewForm}</div><div class="detail-section"><div class="detail-label">WHY THIS MATCH? · AUDITABLE OPTIMIZATION</div>${explanation}</div><div class="detail-actions">${buttons}</div><div class="detail-section" id="draftArea" style="display:none"></div>`;
 $('#approveCase')?.addEventListener('click',()=>action('approve/'+c.id,`Approved ${c.id}; remaining proposals reoptimized.`));
 $('#rejectCase')?.addEventListener('click',()=>action('reject/'+c.id,'Proposal rejected, supplies unchanged.'));
 $('#reopenCase')?.addEventListener('click',()=>action('reopen/'+c.id,'Reopened for another optimization run.'));
 $('#distinctCase')?.addEventListener('click',()=>action('resolve-duplicate/'+c.id,'Case marked distinct and matching recalculated.'));
 $('#escalateCase')?.addEventListener('click',()=>action('escalate/'+c.id,'Safety hold stays active. No emergency call was made by the app.',{confirmed_contacted:false}));
 $('#attestEscalation')?.addEventListener('click',()=>{if(window.confirm('This is a FICTIONAL DEMO attestation. Do not use this app for real emergencies. Do you confirm you contacted emergency services MANUALLY?'))action('escalate/'+c.id,'Manual-contact attestation recorded (demo only). App made no call.',{confirmed_contacted:true})});
 $('#matchThis')?.addEventListener('click',()=>action('match','Exact constrained optimization recalculated.'));
 $('#reviewForm')?.addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.currentTarget);const body={category:f.get('category'),zone:f.get('zone'),demand:Number(f.get('demand'))};try{store=await api('review/'+c.id,'POST',body);render();toast('Human correction saved and proposal recomputed.')}catch(err){toast('Could not review: '+err.message)}});
 $('#previewDraft')?.addEventListener('click',async()=>{try{const data=await api('dispatch-draft/'+c.id);$('#draftArea').style.display='block';$('#draftArea').innerHTML=`<div class="detail-label">UNSENT DRAFT — VERIFY FIRST</div><pre class="draft">${h(data.draft)}</pre><button class="secondary-btn" id="copyDraft">Copy draft to clipboard</button>`;$('#copyDraft').onclick=()=>navigator.clipboard.writeText(data.draft).then(()=>toast('Draft copied. Nothing sent.')).catch(()=>toast('Clipboard permission unavailable'))}catch(e){toast(e.message)}});
}

function openCase(id){activeCase=id;const c=store.cases.find(c=>c.id===id);if(!c)return;renderDetails(c);$('#modalOverlay').classList.remove('hidden');}
function closeCase(){activeCase=null;$('#modalOverlay').classList.add('hidden')}
async function action(path,msg,body=null){try{const result=await api(path,'POST',body);store=result;$('#scenarioResults').innerHTML='<div class="lab-placeholder">Live state changed. Re-run the scenario to compare current plans.</div>';render();toast(msg)}catch(e){toast('Could not complete action: '+e.message)}}
$$('.nav').forEach(b=>b.onclick=()=>{screen=b.dataset.screen;$$('.nav').forEach(x=>x.classList.toggle('active',x===b));$$('.screen').forEach(x=>x.classList.add('hidden'));$('#screen-'+screen).classList.remove('hidden');$('#currentScreen').textContent=screen==='overview'?'COMMAND CENTER':screen==='requests'?'REQUEST INTELLIGENCE':screen==='resources'?'RESOURCE NETWORK':'DECISION TRAIL';window.scrollTo({top:0,behavior:'smooth'})});
$$('.filter').forEach(b=>b.onclick=()=>{filter=b.dataset.filter;$$('.filter').forEach(x=>x.classList.toggle('active',x===b));renderRequests()});
$('#runDemo').onclick=()=>action('import-demo','11 messages analyzed with local ML and duplicate detection.');
$('#resetBtn').onclick=()=>{closeCase();action('reset','Sandbox reset. You can replay the demo.');};
$('#optimizeBtn').onclick=()=>action('match','Solved exact inventory- and capacity-constrained MILP.');
$('#simulateBtn').onclick=runScenario;
$('#intakeForm').onsubmit=async e=>{e.preventDefault();const text=$('#intakeText').value.trim();if(text.length<8){toast('Please enter a longer request');return}try{const r=await api('intake','POST',{message:text});store=r.state;$('#scenarioResults').innerHTML='<div class="lab-placeholder">New request received. Re-run the scenario to compare current plans.</div>';render();$('#intakeText').value='';openCase(r.case.id);toast('AI request analysis complete.')}catch(e){toast('Error: '+e.message)}};
$('#exportBtn').onclick=()=>{const blob=new Blob([JSON.stringify({exported_at:new Date().toISOString(),disclaimer:'Synthetic research prototype — not an emergency-response system',...store},null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='emberline_audit.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('Synthetic workflow report exported.');};
$('#closeModal').onclick=closeCase;$('#modalOverlay').onclick=e=>{if(e.target.id==='modalOverlay')closeCase()};document.addEventListener('keydown',e=>{if(e.key==='Escape')closeCase()});
setInterval(()=>{$('#clock').textContent=new Date().toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit',timeZone:'UTC'})+' UTC'},1000);
api('state').then(s=>{store=s;render();}).catch(e=>toast('Backend unreachable: '+e.message));
