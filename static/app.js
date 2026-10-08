const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const inr=x=>'₹'+Math.round(x).toLocaleString('en-IN');
let kind='car',owners=2,svc='Available',acc='Unknown',files=[],CAT={car:[],bike:[],scooter:[]},cur=null;

document.documentElement.classList.add('js');
function show(v){$$('.view').forEach(e=>e.classList.toggle('on',e.id=='v-'+v));$$('[data-v]').forEach(b=>b.classList.toggle('on',b.dataset.v==v));scrollTo({top:$('#app').offsetTop-64,behavior:'smooth'});if(v=='his')loadHist()}
$$('[data-v]').forEach(b=>b.onclick=()=>show(b.dataset.v));
const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}}),{threshold:.12});$$('.rv').forEach(e=>io.observe(e));

function sug(f=''){const a=(CAT[kind]||[]).filter(n=>n.toLowerCase().includes(f.trim().toLowerCase()));
 $('#sug').innerHTML=a.map(n=>`<button class="chip${n==$('#name').value?' on':''}">${esc(n)}</button>`).join('');
 [...$('#sug').children].forEach(c=>c.onclick=()=>{$('#name').value=c.textContent;sug()})}
const fillModels=()=>sug('');
$('#name').onfocus=()=>{sug('');$('#name').select()};$('#name').oninput=()=>sug($('#name').value);
fetch('/api/catalog').then(r=>r.json()).then(c=>{CAT=c;fillModels()}).catch(()=>{});
$$('#kind button').forEach(b=>b.onclick=()=>{kind=b.dataset.k;$$('#kind button').forEach(x=>x.classList.toggle('on',x==b));fillModels();$('#name').value=(CAT[kind]||[])[0]||''});

function chips(id,opts,get,set){const el=$(id);el.innerHTML=opts.map(o=>`<button class="chip${get()==o?' on':''}">${o}</button>`).join('');
 [...el.children].forEach(c=>c.onclick=()=>{set(c.textContent);chips(id,opts,get,set)})}
chips('#svc',['Available','Partial','Not available','Unknown'],()=>svc,v=>svc=v);
chips('#acc',['No','Yes','Unknown'],()=>acc,v=>acc=v);
$('#om').onclick=()=>{owners=Math.max(1,owners-1);$('#ov').textContent=owners};
$('#op').onclick=()=>{owners=Math.min(6,owners+1);$('#ov').textContent=owners};

const QP=[[25000,'₹25k'],[50000,'₹50k'],[100000,'₹1L'],[300000,'₹3L'],[500000,'₹5L'],[1000000,'₹10L']];
$('#pq').innerHTML=QP.map(([v,l])=>`<button class="chip" data-v="${v}">${l}</button>`).join('');
$$('#pq .chip').forEach(c=>c.onclick=()=>{$('#price').value=c.dataset.v;pw()});
const KQ=[[10000,'10k'],[25000,'25k'],[50000,'50k'],[75000,'75k'],[100000,'1L']];
$('#kq').innerHTML=KQ.map(([v,l])=>`<button class="chip" data-v2="${v}">${l} km</button>`).join('');
$$('#kq .chip').forEach(c=>c.onclick=()=>{$('#km').value=c.dataset.v2;kw()});
function kw(){const v=+$('#km').value;$('#kw').textContent=v>=0&&$('#km').value!==''?v.toLocaleString('en-IN')+' km driven':''}$('#km').oninput=kw;kw();
function pw(){const v=+$('#price').value;$('#pw').textContent=v>0?inr(v):''}$('#price').oninput=pw;pw();

function drawPh(){$('#photos').innerHTML=files.map((f,i)=>`<div class="ph"><img src="${URL.createObjectURL(f)}"><i data-i="${i}">×</i></div>`).join('')+(files.length<5?'<div class="add" id="addp">＋</div>':'');
 $$('.ph i').forEach(x=>x.onclick=()=>{files.splice(+x.dataset.i,1);drawPh()});const a=$('#addp');if(a)a.onclick=()=>$('#file').click()}
$('#file').onchange=e=>{files=files.concat([...e.target.files]).slice(0,5);e.target.value='';drawPh()};drawPh();

const STAGES=['Vehicle details validate ho rahe hain…','Price model fair range nikal raha hai…','Photos check ho rahi hain…','Risk score calculate ho raha hai…','AI report likh raha hai…'];
let tmr;function load(on){$('#ov').classList.toggle('on',on);clearInterval(tmr);if(!on)return;let i=0;$('#pgi').style.width='5%';
 const tick=()=>{$('#os').textContent=STAGES[Math.min(i,4)];$('#pgi').style.width=Math.min(92,8+i*18)+'%';i++};tick();tmr=setInterval(tick,2800)}

$('#go').onclick=async()=>{
 const bad=[['#name',!$('#name').value.trim()],['#year',!(+$('#year').value>=1980)],['#km',$('#km').value===''||+$('#km').value<0],['#price',!(+$('#price').value>=1000)]].filter(x=>x[1]);
 $$('input').forEach(i=>i.classList.remove('err'));
 if(bad.length){bad.forEach(b=>$(b[0]).classList.add('err'));$(bad[0][0]).focus();return toast('Details sahi bharo (price kam se kam ₹1,000)','err')}
 const fd=new FormData();fd.append('name',$('#name').value);fd.append('kind',kind);fd.append('year',$('#year').value);fd.append('km',$('#km').value);
 fd.append('owners',owners);fd.append('price',$('#price').value);fd.append('service_history',svc);fd.append('accident',acc);
 if($('#np').value)fd.append('new_price',$('#np').value);files.forEach(f=>fd.append('images',f));
 load(true);const ac=new AbortController(),to=setTimeout(()=>ac.abort(),100000);
 try{const r=await fetch('/api/analyze',{method:'POST',body:fd,signal:ac.signal});const j=await r.json();
  if(!r.ok)throw new Error(j.detail||'Server error');render(j);show('res')}
 catch(e){toast(e.name=='AbortError'?'Server ne bahut time liya. Thodi der baad dobara try karo (free server sleep se uth raha ho sakta hai).':e.message,'err')}
 finally{clearTimeout(to);load(false)}};

const BAND={'Low Risk':'#22c55e','Moderate Risk':'#eab308','High Risk':'#f97316','Very High Risk':'#ef4444'};
const PC={'FAIR / GOOD':'#22c55e','SLIGHTLY HIGH':'#f59e0b','HIGH':'#ef4444','SUSPICIOUSLY LOW':'#a855f7'};
const col=r=>r<.34?'#22c55e':r<.67?'#f59e0b':'#ef4444';
const ul=a=>'<ul class="l">'+a.map(x=>`<li>${esc(x)}</li>`).join('')+'</ul>';

function odo(v){const T={car:12000,bike:8000,scooter:6000}[v.kind]||10000,L={car:250000,bike:120000,scooter:90000}[v.kind]||150000;
 const py=v.km/Math.max(v.age,1),r=py/T,life=Math.min(100,v.km/L*100),f=n=>Math.round(n).toLocaleString('en-IN');
 const t=r<.6?['Kam use hui','#22c55e','Typical se kam chali hai — odometer reading aur condition dono verify karo.']:r<=1.25?['Normal use','#22c55e','Age ke hisaab se normal chali hai.']:r<=1.7?['Zyada use','#f59e0b','Typical se zyada chali hai — engine, clutch aur suspension ka wear dhyan se check karo.']:['Bahut zyada use','#ef4444','Bahut high running hai — price kam honi chahiye aur mechanic inspection must hai.'];
 return `<div class="card"><h3>🛣️ Odometer insight</h3><div class="big">${f(v.km)} km <span class="mut" style="font-size:14px">driven</span></div>
 <div class="fr" style="margin-top:10px"><span>Per year: <b>${f(py)} km</b> (typical ~${f(T)})</span><b style="color:${t[1]}">${t[0]}</b></div><div class="fb"><i data-w="${Math.min(100,r/2*100)}" style="background:${t[1]}"></i></div>
 <div class="fr"><span>Estimated life used (~${f(L)} km)</span><b>${Math.round(life)}%</b></div><div class="fb"><i data-w="${life}" style="background:${col(life/100)}"></i></div><div class="mut">${t[2]}</div></div>`}
function render(r){cur=r;const v=r.vehicle,p=r.price,k=r.risk,rep=r.report,bc=BAND[k.label]||'#eab308',pc=PC[p.label]||'#f59e0b';
 const lo=Math.min(p.asking,p.fair_low)*.85,hi=Math.max(p.asking,p.fair_high)*1.15,pos=x=>Math.max(0,Math.min(100,(x-lo)/(hi-lo)*100));
 const ico={car:'🚗',bike:'🏍️',scooter:'🛵'}[v.kind]||'🚘',sev={none:'#22c55e',minor:'#f59e0b',possible_concern:'#ef4444'};
 const ckKey='ck'+(r.id||'x'),saved=JSON.parse(localStorage.getItem(ckKey)||'[]');
 $('#v-res').innerHTML=`<div class="rtabs"><button class="on" data-t="0">Overview</button><button data-t="1">Risk &amp; photos</button><button data-t="2">Action plan</button></div><div class="tp on" data-t="0">
 <div class="card center"><svg class="gauge" viewBox="0 0 200 120" style="width:100%;max-width:280px"><path d="M20 100A80 80 0 0 1 180 100" fill="none" stroke="var(--bd)" stroke-width="16" stroke-linecap="round"/>
  <path class="v" id="gv" d="M20 100A80 80 0 0 1 180 100" fill="none" stroke="${bc}" stroke-width="16" stroke-linecap="round" stroke-dasharray="0 251.3"/>
  <text x="100" y="94" text-anchor="middle" font-size="40" font-weight="800" fill="currentColor" id="gn">0</text><text x="100" y="114" text-anchor="middle" font-size="12" fill="var(--mut)">out of 100</text></svg>
  <div class="big" style="color:${bc}">${k.emoji} ${esc(k.label)}</div><div class="mut" style="margin-top:6px">${esc(rep.summary||'')}</div>
  <div style="margin-top:12px"><button class="chip" id="sh">📤 Share</button> <button class="chip" id="pr">🖨️ Save PDF</button></div></div>
 <div class="card"><h3>${ico} ${esc(v.name)}</h3><div class="mut">${v.year} · ${v.age} yrs · ${v.km.toLocaleString('en-IN')} km · ${v.owners} owner(s)</div>
  <div style="margin-top:8px"><span class="tag" style="background:var(--bg)">Service: ${esc(v.service)}</span><span class="tag" style="background:var(--bg)">Accident: ${esc(v.accident)}</span></div></div>
 ${odo(v)}<div class="card"><h3>💰 Price check</h3><div class="big" style="color:${pc}">${esc(p.label)}</div>
  <div class="mut">Asking ${inr(p.asking)} · Fair ${inr(p.fair_low)} – ${inr(p.fair_high)}</div>
  <div class="pm"><div class="f" style="left:${pos(p.fair_low)}%;width:${pos(p.fair_high)-pos(p.fair_low)}%"></div><em style="left:${(pos(p.fair_low)+pos(p.fair_high))/2}%;top:20px;color:#22c55e">fair range</em>
  <div class="a" style="left:${pos(p.asking)}%;background:${pc}"></div><em style="left:${pos(p.asking)}%;top:-28px;color:${pc}">asking ${inr(p.asking)}</em></div>
  <div class="mut">Demo model (synthetic data) — approximate hai.</div></div>
 </div><div class="tp" data-t="1"><div class="card"><h3>📉 Risk breakdown</h3>${Object.entries(k.parts).map(([a,x])=>`<div class="fr"><span>${esc(a)}</span><b>${x}/${k.max[a]}</b></div><div class="fb"><i data-w="${x/k.max[a]*100}" style="background:${col(x/k.max[a])}"></i></div>`).join('')}</div>
 <div class="card"><h3>📷 Photo observations</h3>${r.vision.length?'<ul class="l" style="list-style:none;padding:0">'+r.vision.map(o=>`<li><span class="tag" style="background:${sev[o.severity]||'#888'}33;color:${sev[o.severity]||'#888'}">${esc((o.severity||'').replace('_',' '))}</span><b>${esc(o.area)}</b>: ${esc(o.observation)}</li>`).join('')+'</ul><div class="mut">Possible signs only — diagnosis nahi.</div>':`<div class="mut">${esc(r.vision_status)}</div>`}</div>
 <div class="card" style="border-color:#ef444466"><h3>⚠️ Concerns</h3>${ul(rep.concerns)}</div>
 <div class="card" style="border-color:#22c55e66"><h3>✅ Positives</h3>${ul(rep.positives)}</div>
 </div><div class="tp" data-t="2"><div class="card"><h3>🔍 Questions for seller</h3>${ul(rep.seller_questions)}</div>
 <div class="card ck"><h3>🔧 Pre-purchase checklist</h3>${rep.checklist.map((x,i)=>`<label><input type="checkbox" data-i="${i}" ${saved.includes(i)?'checked':''}>${esc(x)}</label>`).join('')}</div>
 <div class="card"><h3>💬 Ask AI</h3><div id="chat"></div><div class="row" style="margin-top:8px"><input id="q" placeholder="e.g. Bumper repaint kaise check karun?" style="flex:4"><button class="go" id="ask" style="flex:1;padding:12px;font-size:14px;box-shadow:none">Ask</button></div></div>
 </div><div class="mut center" style="padding:6px 0 14px">AI estimate hai. Khareedne se pehle mechanic inspection zaroor karwao.${r.timings?` · ${r.timings.report}s`:''}</div>`;
 requestAnimationFrame(()=>requestAnimationFrame(()=>{$('#gv').setAttribute('stroke-dasharray',`${251.3*k.total/100} 251.3`);$$('.fb i').forEach(i=>i.style.width=i.dataset.w+'%');
  let n=0;const t=setInterval(()=>{n+=Math.max(1,Math.round(k.total/30));if(n>=k.total){n=k.total;clearInterval(t)}$('#gn').textContent=n},35)}));
 $$('.rtabs button').forEach(b=>b.onclick=()=>{$$('.rtabs button').forEach(x=>x.classList.toggle('on',x==b));
  $$('.tp').forEach(t=>t.classList.toggle('on',t.dataset.t==b.dataset.t));scrollTo({top:$('#app').offsetTop-8,behavior:'smooth'});
  $$('.tp.on .fb i').forEach(i=>{i.style.width=0;requestAnimationFrame(()=>requestAnimationFrame(()=>i.style.width=i.dataset.w+'%'))})});
 $$('.ck input').forEach(c=>c.onchange=()=>{const s=$$('.ck input').filter(x=>x.checked).map(x=>+x.dataset.i);localStorage.setItem(ckKey,JSON.stringify(s))});
 $('#pr').onclick=()=>{$$('.rtabs button')[0].click();print()};
 $('#sh').onclick=()=>{const t=`${v.name} (${v.year}) – Risk ${k.total}/100 (${k.label}). Asking ${inr(p.asking)}, fair ${inr(p.fair_low)}–${inr(p.fair_high)} (${p.label}).`;navigator.share?navigator.share({title:'VehicleCheck',text:t}).catch(()=>{}):(navigator.clipboard.writeText(t),toast('Summary copy ho gaya ✅','ok'))};
 const send=async()=>{const q=$('#q').value.trim();if(!q||!r.id)return;$('#q').value='';const c=$('#chat');c.insertAdjacentHTML('beforeend',`<div class="bub me">${esc(q)}</div><div class="bub ai" id="pend">…</div>`);
  try{const x=await fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:r.id,question:q})});const j=await x.json();$('#pend').textContent=j.answer||j.detail}catch(e){$('#pend').textContent='Error: '+e.message}$('#pend').removeAttribute('id')};
 $('#ask').onclick=send;$('#q').onkeydown=e=>{if(e.key=='Enter')send()}}

async function loadHist(){try{const h=await (await fetch('/api/history')).json();
 $('#hl').innerHTML=h.length?h.map(x=>`<div class="hi" data-id="${x.id}"><div><b>${esc(x.vehicle)}</b><div class="mut">${esc(x.created.slice(0,16).replace('T',' '))}</div></div><span class="tag" style="background:${BAND[x.label]||'#888'}33;color:${BAND[x.label]||'#888'}">${x.score}/100</span></div>`).join(''):'Abhi koi history nahi.';
 $$('.hi').forEach(e=>e.onclick=async()=>{const r=await (await fetch('/api/reports/'+e.dataset.id)).json();r.id=+e.dataset.id;render(r);show('res')})}catch(e){$('#hl').textContent='History load nahi hui.'}}

/* ---------- app chrome: toast, theme, scroll progress, back-to-top ---------- */
function toast(m,t){const e=document.createElement('div');e.className='toast '+(t||'');e.textContent=m;$('#ts').appendChild(e);setTimeout(()=>e.classList.add('out'),3200);setTimeout(()=>e.remove(),3600)}
const root=document.documentElement,dark=()=>(root.dataset.theme||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light'))=='dark';
if(localStorage.getItem('th'))root.dataset.theme=localStorage.getItem('th');
const th=()=>{$('#th').textContent=dark()?'☀️':'🌙'};th();
$('#th').onclick=()=>{root.dataset.theme=dark()?'light':'dark';localStorage.setItem('th',root.dataset.theme);th()};
addEventListener('scroll',()=>{const h=document.documentElement;$('#sp').style.width=(scrollY/(h.scrollHeight-h.clientHeight||1)*100)+'%';$('#bt').classList.toggle('on',scrollY>600)},{passive:true});
$('#bt').onclick=()=>scrollTo({top:0,behavior:'smooth'});
