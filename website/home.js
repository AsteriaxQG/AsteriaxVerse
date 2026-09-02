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
  function addedTime(ship){const t=Number(ship?.date_added);return Number.isFinite(t)&&t>0?t*1000:0}
  function findStateVehicle(feedShip){
    if(typeof state==='undefined'||!Array.isArray(state.vehicles))return null;
    const target=keyName(feedShip?.name);if(!target)return null;
    let exact=state.vehicles.find(v=>[v.name,v.name_full].some(n=>keyName(n)===target));if(exact)return exact;
    if(target.length<6)return null;
    return state.vehicles.find(v=>[v.name,v.name_full].some(n=>{const k=keyName(n);return k.length>=6&&(k.endsWith(target)||target.endsWith(k))}))||null;
  }

  function latestDatabaseShips(){
    if(typeof query!=='function'||typeof state==='undefined'||!state.db)return[];
    try{
      const rows=query(`SELECT id,name,name_full,manufacturer,is_ground_vehicle,is_concept,url_photo,roles,scu,crew,date_added FROM vehicles WHERE COALESCE(is_ground_vehicle,0)=0 ORDER BY date_added DESC LIMIT 3`);
      return rows.map(row=>{
        const feed=shipFeed.find(x=>keyName(x?.name)===keyName(row?.name));
        if(!feed)return row;
        return Object.assign(row,{name:feed.name||row.name,name_full:feed.name||row.name,manufacturer:feed.manufacturer||row.manufacturer,production_status:feed.status||'',in_game:feed.in_game===true,catalog_image:feed.image||row.url_photo,catalog_description:feed.description||'',rsi_url:feed.rsi_url||'',store_url:feed.store_url||'',pledge_available:feed.pledge_available,pledge_collector:feed.pledge_collector===true,pledge_price:feed.pledge_price,pledge_currency:feed.pledge_currency||'',pledge_is_warbond:feed.pledge_is_warbond===true,pledge_discounted:feed.pledge_discounted===true,pledge_price_kind:feed.pledge_price_kind||''});
      });
    }catch{return[]}
  }

  function pickFeaturedShips(){
    if(typeof state==='undefined'||!Array.isArray(state.vehicles)||!state.vehicles.length)return[];
    const officialNewest=['s65stingray','basher','tyilui'].map(wanted=>state.vehicles.find(v=>[v.name,v.name_full].some(name=>keyName(name)===wanted))).filter(Boolean);
    if(officialNewest.length===3)return officialNewest;
    const picked=[],used=new Set();
    if(shipFeed.length){
      const sorted=shipFeed.filter(v=>String(v.status).toLowerCase()==='flight-ready'&&!isGroundFeed(v)).map(feedShip=>({feedShip,v:findStateVehicle(feedShip)})).filter(x=>x.v&&!Number(x.v.is_ground_vehicle)).sort((a,b)=>addedTime(b.v)-addedTime(a.v));
      for(const entry of sorted){
        const v=entry.v;if(used.has(String(v.id)))continue;
        picked.push(v);used.add(String(v.id));if(picked.length===3)break;
      }
    }
    const fallback=state.vehicles.filter(v=>!used.has(String(v.id))&&Number(v.is_ground_vehicle)!==1&&statusGroup(v)==='flight').sort((a,b)=>addedTime(b)-addedTime(a));
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
    try{const data=await window.AsteriaxApi.getJson('/api/ships',{ttlMs:120000});if(data.ok&&Array.isArray(data.items)){shipFeed=data.items;renderFeaturedShips()}}catch(e){console.warn('Catalogue RSI indisponible',e)}
  }

  function waitForShips(tries=0){const count=(typeof state!=='undefined'&&Array.isArray(state.vehicles))?state.vehicles.length:0;if(count&&renderFeaturedShips())return;if(tries<30)setTimeout(()=>waitForShips(tries+1),250)}

  q('#homePlayers')?.closest('div')?.remove();
  renderHangarSummary();loadHomeNews();loadShipFeed();waitForShips();
  document.addEventListener('click',e=>{if(e.target.closest('[data-card-owned],[data-card-wish],[data-hangar-owned],[data-hangar-wish]'))setTimeout(renderHangarSummary,30)});
  window.addEventListener('storage',renderHangarSummary);
})();

