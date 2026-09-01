(()=>{
  const q=s=>document.querySelector(s);
  const escHome=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const labels={'PATCH':'PATCH','ROADMAP':'ROADMAP','SNEAK PEEK':'SNEAK PEEK','VIDEO':'VIDÉO','KNOWN ISSUE':'KNOWN ISSUE','NEWS':'ACTU'};
  const norm=v=>String(v??'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');

  function postedLabel(value=''){
    const text=String(value).trim();
    const match=text.match(/^(\d+|an?|one)\s+(minute|hour|day|week|month|year)s?\s+ago$/i);
    if(!match)return text;
    const amount=/^(?:a|an|one)$/i.test(match[1])?1:Number(match[1]);
    const units={minute:['minute','minutes'],hour:['heure','heures'],day:['jour','jours'],week:['semaine','semaines'],month:['mois','mois'],year:['an','ans']};
    const unit=units[match[2].toLowerCase()];
    return `il y a ${amount} ${unit[amount===1?0:1]}`;
  }

  function readSet(key){
    try{return new Set(JSON.parse(localStorage.getItem(key)||'[]').map(String))}catch{return new Set()}
  }

  function renderHangarSummary(){
    const owned=readSet('ax_hangar_owned'),wish=readSet('ax_hangar_wishlist');
    const ownedEl=q('#homeOwnedCount'),wishEl=q('#homeWishCount');
    if(ownedEl)ownedEl.textContent=owned.size.toLocaleString('fr-FR');
    if(wishEl)wishEl.textContent=wish.size.toLocaleString('fr-FR');
  }

  function statusGroup(v){
    const raw=norm(v?.production_status).replace(/[_\s]+/g,'-');
    if(raw.includes('concept'))return'concept';
    if(raw.includes('active-production')||raw.includes('long-term-production')||raw==='production'||raw.includes('in-production'))return'production';
    if(raw.includes('flight-ready')||raw.includes('hangar-ready')||Number(v?.price_min)>0||v?.in_game===true||v?.in_game===1)return'flight';
    return'other';
  }

  function hasImage(v){return Boolean(String(v?.catalog_image||v?.url_photo||'').trim())}

  function bestByStatus(list,status,used){
    const preferred=['Polaris','Zeus Mk II','C1 Spirit','Vulture','Corsair','Intrepid','Starlancer','Guardian','Perseus','Galaxy','Merchantman','Railen'];
    const candidates=list.filter(v=>!used.has(String(v.id))&&Number(v.is_ground_vehicle)!==1&&statusGroup(v)===status&&hasImage(v));
    for(const name of preferred){const hit=candidates.find(v=>norm(v.name).includes(norm(name)));if(hit)return hit}
    return candidates[0]||null;
  }

  function pickFeaturedShips(){
    if(typeof state==='undefined'||!Array.isArray(state.vehicles))return[];
    const all=state.vehicles.filter(v=>Number(v.is_ground_vehicle)!==1);
    const used=new Set(),picked=[];
    for(const s of ['flight','production','concept']){
      const v=bestByStatus(all,s,used);if(v){picked.push(v);used.add(String(v.id))}
    }
    const fallback=all.filter(v=>!used.has(String(v.id))&&hasImage(v)).sort((a,b)=>String(a.name||'').localeCompare(String(b.name||''),'fr',{numeric:true}));
    while(picked.length<3&&fallback.length){const v=fallback.shift();if(!used.has(String(v.id))){picked.push(v);used.add(String(v.id))}}
    return picked.slice(0,3);
  }

  function renderFeaturedShips(){
    const grid=q('#homeShipGrid');if(!grid||typeof vehicleCard!=='function')return false;
    const list=pickFeaturedShips();if(!list.length)return false;
    grid.innerHTML=list.map(vehicleCard).join('');
    if(typeof bindCards==='function')bindCards(grid);
    return true;
  }

  function newsCard(x){
    const image=x.image?`<div class="home-news-image"><img loading="lazy" src="${escHome(x.image)}" alt="" referrerpolicy="no-referrer"></div>`:'<div class="home-news-image"><span>ASTERIAXVERSE</span></div>';
    return `<a class="home-news-card" href="${escHome(x.url||'https://robertsspaceindustries.com/en/comm-link')}" target="_blank" rel="noopener">${image}<div class="home-news-body"><div class="home-news-meta"><span>${escHome(labels[x.category]||x.category||'ACTU')}</span><time>${escHome(postedLabel(x.posted||''))}</time></div><h3>${escHome(x.title||'Publication Star Citizen')}</h3><p>${escHome(x.excerpt||'Publication officielle Roberts Space Industries.')}</p></div></a>`;
  }

  function renderNow(items){
    const grid=q('#homeNowGrid');if(!grid)return;
    const picks=[];
    for(const category of ['PATCH','ROADMAP','NEWS','VIDEO','SNEAK PEEK']){
      const hit=items.find(x=>x.category===category&&!picks.includes(x));if(hit)picks.push(hit);if(picks.length===3)break;
    }
    for(const x of items){if(picks.length===3)break;if(!picks.includes(x))picks.push(x)}
    grid.innerHTML=picks.length?picks.map(x=>`<div class="home-now-card"><span>${escHome(labels[x.category]||x.category||'ACTU')}</span><strong>${escHome(x.title||'Publication officielle')}</strong><small>${escHome(postedLabel(x.posted||''))}</small></div>`).join(''):'<div class="home-loading">Les informations officielles sont en cours de chargement.</div>';
  }

  function updateHeroPatch(items){
    const patch=items.find(x=>x.category==='PATCH')||items[0];
    const title=q('#homePatchTitle'),posted=q('#homePatchPosted');
    if(!patch)return;
    if(title)title.textContent=patch.title||'Dernière publication RSI';
    if(posted)posted.textContent=postedLabel(patch.posted||'');
  }

  async function loadHomeNews(){
    const grid=q('#homeNewsGrid');if(!grid)return;
    try{
      const res=await fetch(`/api/news?ts=${Date.now()}`,{headers:{Accept:'application/json'},cache:'no-store'});
      if(!res.ok)throw new Error('API indisponible');
      const data=await res.json();if(!data.ok||!Array.isArray(data.items)||!data.items.length)throw new Error('Aucune actualité');
      const items=data.items;
      grid.innerHTML=items.slice(0,3).map(newsCard).join('');
      updateHeroPatch(items);renderNow(items);
    }catch(e){
      grid.innerHTML=`<a class="home-news-card" href="https://robertsspaceindustries.com/en/comm-link" target="_blank" rel="noopener"><div class="home-news-image"><span>COMM-LINK</span></div><div class="home-news-body"><div class="home-news-meta"><span>ACTU</span></div><h3>Actualités officielles Star Citizen</h3><p>Le flux automatique est temporairement indisponible.</p></div></a>`;
      const now=q('#homeNowGrid');if(now)now.innerHTML='<div class="home-loading">Flux officiel temporairement indisponible.</div>';
    }
  }

  function waitForShips(tries=0,lastCount=0){
    const count=(typeof state!=='undefined'&&Array.isArray(state.vehicles))?state.vehicles.length:0;
    if(count&&renderFeaturedShips()){
      if(tries<12)setTimeout(()=>waitForShips(tries+1,count),800);
      return;
    }
    if(tries<25)setTimeout(()=>waitForShips(tries+1,count),250);
  }

  renderHangarSummary();loadHomeNews();waitForShips();
  document.addEventListener('click',e=>{if(e.target.closest('[data-card-owned],[data-card-wish],[data-hangar-owned],[data-hangar-wish]'))setTimeout(renderHangarSummary,30)});
  window.addEventListener('storage',renderHangarSummary);
})();