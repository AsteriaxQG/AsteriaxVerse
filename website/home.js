(()=>{
  const q=s=>document.querySelector(s);
  const escHome=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const labels={'PATCH':'PATCH','ROADMAP':'ROADMAP','SNEAK PEEK':'SNEAK PEEK','VIDEO':'VIDÉO','KNOWN ISSUE':'KNOWN ISSUE','NEWS':'ACTU'};
  const norm=v=>String(v??'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
  const keyName=v=>norm(v).replace(/\s+/g,'');
  let homeNewsItems=[];
  let shipFeed=[];

  function postedLabel(value=''){
    const text=String(value).trim();
    const match=text.match(/^(\d+|an?|one)\s+(minute|hour|day|week|month|year)s?\s+ago$/i);
    if(!match)return text;
    const amount=/^(?:a|an|one)$/i.test(match[1])?1:Number(match[1]);
    const units={minute:['minute','minutes'],hour:['heure','heures'],day:['jour','jours'],week:['semaine','semaines'],month:['mois','mois'],year:['an','ans']};
    const unit=units[match[2].toLowerCase()];
    return `il y a ${amount} ${unit[amount===1?0:1]}`;
  }

  function readSet(key){try{return new Set(JSON.parse(localStorage.getItem(key)||'[]').map(String))}catch{return new Set()}}
  function renderHangarSummary(){const owned=readSet('ax_hangar_owned'),wish=readSet('ax_hangar_wishlist');if(q('#homeOwnedCount'))q('#homeOwnedCount').textContent=owned.size.toLocaleString('fr-FR');if(q('#homeWishCount'))q('#homeWishCount').textContent=wish.size.toLocaleString('fr-FR')}

  function statusGroup(v){
    const raw=norm(v?.production_status).replace(/\s+/g,'-');
    if(raw.includes('flight-ready')||raw.includes('hangar-ready')||Number(v?.price_min)>0||v?.in_game===true||v?.in_game===1)return'flight';
    if(raw.includes('concept'))return'concept';
    if(raw.includes('active-production')||raw.includes('long-term-production')||raw==='production'||raw.includes('in-production'))return'production';
    return'other';
  }

  function isGroundFeed(v){const s=norm(`${v?.type||''} ${v?.size||''}`);return /(^| )(ground|ground vehicle|vehicle)( |$)/.test(s)}
  function shipMentionIndex(ship){
    const name=norm(ship?.name);if(name.length<5)return Number.MAX_SAFE_INTEGER;
    const key=keyName(name);
    for(let i=0;i<homeNewsItems.length;i++){
      const hay=norm(`${homeNewsItems[i].title||''} ${homeNewsItems[i].excerpt||''}`);
      const compact=keyName(hay);
      if(hay.includes(name)||compact.includes(key))return i;
    }
    return Number.MAX_SAFE_INTEGER;
  }
  function updatedTime(ship){const t=Date.parse(ship?.updated||'');return Number.isFinite(t)?t:0}
  function findStateVehicle(feedShip){
    if(typeof state==='undefined'||!Array.isArray(state.vehicles))return null;
    const target=keyName(feedShip?.name);if(!target)return null;
    let exact=state.vehicles.find(v=>[v.name,v.name_full].some(n=>keyName(n)===target));if(exact)return exact;
    if(target.length<6)return null;
    return state.vehicles.find(v=>[v.name,v.name_full].some(n=>{const k=keyName(n);return k.length>=6&&(k.endsWith(target)||target.endsWith(k))}))||null;
  }

  function pickFeaturedShips(){
    if(typeof state==='undefined'||!Array.isArray(state.vehicles)||!state.vehicles.length)return[];
    const picked=[],used=new Set();
    if(shipFeed.length){
      const sorted=shipFeed.filter(v=>String(v.status).toLowerCase()==='flight-ready'&&!isGroundFeed(v)).sort((a,b)=>updatedTime(b)-updatedTime(a));
      for(const feedShip of sorted){
        const v=findStateVehicle(feedShip);if(!v||used.has(String(v.id))||Number(v.is_ground_vehicle)===1)continue;
        picked.push(v);used.add(String(v.id));if(picked.length===3)break;
      }
    }
    const fallback=state.vehicles.filter(v=>!used.has(String(v.id))&&Number(v.is_ground_vehicle)!==1&&statusGroup(v)==='flight').sort((a,b)=>String(a.name||'').localeCompare(String(b.name||''),'fr',{numeric:true}));
    while(picked.length<3&&fallback.length){const v=fallback.shift();if(!used.has(String(v.id))){picked.push(v);used.add(String(v.id))}}
    return picked.slice(0,3);
  }

  function renderFeaturedShips(){
    const grid=q('#homeShipGrid');if(!grid||typeof vehicleCard!=='function')return false;
    const list=pickFeaturedShips();if(!list.length)return false;
    grid.innerHTML=list.map(vehicleCard).join('');if(typeof bindCards==='function')bindCards(grid);return true;
  }

  function newsCard(x){
    const image=x.image?`<div class="home-news-image"><img loading="lazy" src="${escHome(x.image)}" alt="" referrerpolicy="no-referrer"></div>`:'<div class="home-news-image"><span>ASTERIAXVERSE</span></div>';
    return `<a class="home-news-card" href="${escHome(x.url||'https://robertsspaceindustries.com/en/comm-link')}" target="_blank" rel="noopener">${image}<div class="home-news-body"><div class="home-news-meta"><span>${escHome(labels[x.category]||x.category||'ACTU')}</span><time>${escHome(postedLabel(x.posted||''))}</time></div><h3>${escHome(x.title||'Publication Star Citizen')}</h3><p>${escHome(x.excerpt||'Publication officielle Roberts Space Industries.')}</p></div></a>`;
  }

  function renderNow(items){
    const grid=q('#homeNowGrid');if(!grid)return;const picks=[];
    for(const category of ['PATCH','ROADMAP','NEWS','VIDEO','SNEAK PEEK']){const hit=items.find(x=>x.category===category&&!picks.includes(x));if(hit)picks.push(hit);if(picks.length===3)break}
    for(const x of items){if(picks.length===3)break;if(!picks.includes(x))picks.push(x)}
    grid.innerHTML=picks.length?picks.map(x=>`<div class="home-now-card"><span>${escHome(labels[x.category]||x.category||'ACTU')}</span><strong>${escHome(x.title||'Publication officielle')}</strong><small>${escHome(postedLabel(x.posted||''))}</small></div>`).join(''):'<div class="home-loading">Les informations officielles sont en cours de chargement.</div>';
  }

  function updateHeroPatch(items){const patch=items.find(x=>x.category==='PATCH')||items[0];if(!patch)return;if(q('#homePatchTitle'))q('#homePatchTitle').textContent=patch.title||'Dernière publication RSI';if(q('#homePatchPosted'))q('#homePatchPosted').textContent=postedLabel(patch.posted||'')}

  async function loadHomeNews(){
    const grid=q('#homeNewsGrid');if(!grid)return;
    try{
      const data=await window.AsteriaxApi.getJson('/api/news',{ttlMs:120000});if(!data.ok||!Array.isArray(data.items)||!data.items.length)throw new Error('Aucune actualité');
      homeNewsItems=data.items;grid.innerHTML=homeNewsItems.slice(0,3).map(newsCard).join('');updateHeroPatch(homeNewsItems);renderNow(homeNewsItems);renderFeaturedShips();
    }catch(e){
      grid.innerHTML=`<a class="home-news-card" href="https://robertsspaceindustries.com/en/comm-link" target="_blank" rel="noopener"><div class="home-news-image"><span>COMM-LINK</span></div><div class="home-news-body"><div class="home-news-meta"><span>ACTU</span></div><h3>Actualités officielles Star Citizen</h3><p>Le flux automatique est temporairement indisponible.</p></div></a>`;
      if(q('#homeNowGrid'))q('#homeNowGrid').innerHTML='<div class="home-loading">Flux officiel temporairement indisponible.</div>';
    }
  }

  async function loadShipFeed(){
    try{const data=await window.AsteriaxApi.getJson('/api/ships',{ttlMs:120000});if(data.ok&&Array.isArray(data.items)){shipFeed=data.items;renderFeaturedShips()}}catch(e){console.warn('Derniers Flight Ready indisponibles',e)}
  }

  function tone(value=''){const s=norm(value);if(s.includes('operationnel')||s.includes('en ligne'))return'good';if(s.includes('incident majeur')||s.includes('hors ligne'))return'bad';if(s.includes('degrade')||s.includes('maintenance')||s.includes('incident partiel'))return'warn';return''}
  function setEnv(prefix,data,label){
    const status=data?.status||((prefix==='Ptu'||prefix==='Eptu')?'Hors ligne':'Inconnu'),version=data?.version?`Alpha ${data.version}`:'—',build=data?.build||label;
    const statusEl=q(`#home${prefix}Status`),versionEl=q(`#home${prefix}Version`),buildEl=q(`#home${prefix}Build`);
    if(statusEl){statusEl.textContent=status;statusEl.className=tone(status)}if(versionEl)versionEl.textContent=version;if(buildEl){buildEl.textContent=build;buildEl.title=build}
  }
  async function loadUniverseStatus(){
    try{
      const data=await window.AsteriaxApi.getJson('/api/status',{ttlMs:15000});if(!data.ok)throw new Error('Statut incomplet');
      setEnv('Live',data.live,'Version LIVE officielle');setEnv('Ptu',data.ptu,'Public Test Universe');setEnv('Eptu',data.eptu,'Experimental PTU');
      if(q('#homePuStatus'))q('#homePuStatus').textContent=data.services?.persistentUniverse||'Inconnu';if(q('#homePlatformStatus'))q('#homePlatformStatus').textContent=data.services?.platform||'Inconnu';if(q('#homeArenaStatus'))q('#homeArenaStatus').textContent=data.services?.arenaCommander||'Inconnu';
      const overall=q('#verseOverallStatus'),overallText=data.live?.status||data.services?.persistentUniverse||'Inconnu';if(overall){overall.textContent=overallText;overall.className=`verse-overall ${tone(overallText)}`}
      if(q('#verseStatusSummary'))q('#verseStatusSummary').textContent=`Persistent Universe : ${data.services?.persistentUniverse||'Inconnu'} · LIVE ${data.live?.version?`Alpha ${data.live.version}`:'version inconnue'}`;
      if(q('#verseSourceNote')){const d=new Date(data.updatedAt);q('#verseSourceNote').textContent=`Sources officielles RSI · actualisé ${d.toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'})}`}
    }catch(e){
      const overall=q('#verseOverallStatus');if(overall){overall.textContent='Statut indisponible';overall.className='verse-overall warn'}if(q('#verseStatusSummary'))q('#verseStatusSummary').textContent='Impossible de joindre les sources de statut officielles pour le moment.';
    }
  }

  function waitForShips(tries=0){const count=(typeof state!=='undefined'&&Array.isArray(state.vehicles))?state.vehicles.length:0;if(count&&renderFeaturedShips())return;if(tries<30)setTimeout(()=>waitForShips(tries+1),250)}

  q('#homePlayers')?.closest('div')?.remove();
  renderHangarSummary();loadHomeNews();loadShipFeed();loadUniverseStatus();waitForShips();
  setInterval(loadUniverseStatus,120000);
  document.addEventListener('click',e=>{if(e.target.closest('[data-card-owned],[data-card-wish],[data-hangar-owned],[data-hangar-wish]'))setTimeout(renderHangarSummary,30)});
  window.addEventListener('storage',renderHangarSummary);
})();

