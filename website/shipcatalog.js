(()=>{
const owned=new Set(JSON.parse(localStorage.getItem('ax_hangar_owned')||'[]'));
const wished=new Set(JSON.parse(localStorage.getItem('ax_hangar_wishlist')||'[]'));
let ready=false,hangarMode='owned';
const human=(v,depth=0)=>{if(v===null||v===undefined||depth>4)return'';if(typeof v==='string'||typeof v==='number'||typeof v==='boolean')return String(v).trim();if(Array.isArray(v))return v.map(x=>human(x,depth+1)).find(Boolean)||'';if(typeof v==='object'){for(const k of ['name','display_name','label','value','title','code','slug','status','type','size','url','src']){const t=human(v[k],depth+1);if(t)return t}}return''};
const normName=v=>human(v).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
const NON_HULL_ENTRIES=new Set(['valkyrie liberator edition','valkyrie 2948 liberator edition','anvil valkyrie liberator edition','anvil valkyrie 2948 liberator edition','carrack w c8x','carrack expedition w c8x']);
const MATCH_ALIASES=new Map([
 ['gladiuspirateedition','gladiuspirate'],['gladiuspirate','gladiuspirate'],
 ['genesisstarliner','genesis'],['genesis','genesis'],
 ['novatank','nova'],['nova','nova'],
 ['mercurystarrunner','mercury'],['mercury','mercury'],
 ['c8rpiscesrescue','c8rpisces'],['c8rpisces','c8rpisces'],
 ['aresinfernostarfighter','aresinferno'],['aresinferno','aresinferno'],
 ['aresionstarfighter','aresion'],['aresion','aresion'],
 ['s65stingray','stingray'],['stingray','stingray']
]);
const normalizedName=v=>human(v?.name_full)||human(v?.name)||'';
const catalogKey=v=>normName(normalizedName(v));
function catalogMatchKey(v){let n=normName(v);for(const prefix of ['aegis dynamics ','anvil aerospace ','argo astronautics ','banu ','crusader industries ','drake interplanetary ','kruger intergalactic ','misc ','origin jumpworks ','roberts space industries ','rsi ','tumbril land systems ','tumbril ']){if(n.startsWith(prefix)){n=n.slice(prefix.length);break}}n=n.replace(/\bstarlifter\b/g,' ').replace(/\s+/g,' ').trim().replace(/[^a-z0-9]/g,'');return MATCH_ALIASES.get(n)||n}
function sourceStatus(v){return human(v?.production_status)||(Number(v?.is_concept)===1?'concept':'unknown')}
function effectiveStatus(v){const s=sourceStatus(v).toLowerCase().replace(/_/g,'-').replace(/\s+/g,'-');if(s==='flight-ready'||s==='flightready'||s==='hangar-ready'||s==='hangarready')return'flight-ready';if(s==='active-production'||s==='activeproduction')return'active-production';if(s==='long-term-production'||s==='longtermproduction')return'long-term-production';if(s==='in-concept'||s==='inconcept'||s==='concept')return'concept';if(Number(v?.price_min)>0||v?.in_game===true||v?.in_game===1||String(v?.in_game)==='true')return'flight-ready';return'unknown'}
const statusLabel=s=>({"flight-ready":"Flight Ready","active-production":"Active Production","long-term-production":"Long Term Production","concept":"In Concept","unknown":"Statut non renseigné"}[human(s)]||human(s)||'Statut non renseigné');
const statusClass=s=>human(s).toLowerCase().replace(/[^a-z0-9]+/g,'-')||'unknown';
const key=v=>String(v.id);
const save=()=>{localStorage.setItem('ax_hangar_owned',JSON.stringify([...owned]));localStorage.setItem('ax_hangar_wishlist',JSON.stringify([...wished]))};
function setHangar(id,mode){id=String(id);if(mode==='owned'){owned.has(id)?owned.delete(id):owned.add(id);wished.delete(id)}else{wished.has(id)?wished.delete(id):wished.add(id);owned.delete(id)}save();renderVehicles();renderHangar();toast(mode==='owned'?(owned.has(id)?'Ajouté à mes vaisseaux':'Retiré de mes vaisseaux'):(wished.has(id)?'Ajouté à la wishlist':'Retiré de la wishlist'))}
function imageOf(v){return imgUrl(human(v.catalog_image)||human(v.url_photo))}
function inGamePurchase(v){return Number(v?.price_min)>0?'Disponible':'Indisponible'}
function pledgePurchase(v){return v?.pledge_available===true?'Disponible':v?.pledge_available===false?'Indisponible actuellement':'Non vérifié'}
function availability(v){const s=effectiveStatus(v);if(s==='flight-ready')return'Disponible en jeu';if(s==='active-production')return'En production';if(s==='long-term-production')return'Production planifiée';if(s==='concept')return'En concept';return'Statut non renseigné'}
function fallbackImage(name){return `<div class="image-fallback ship-fallback"><strong>${esc(name||'Vaisseau')}</strong><small>Image en attente</small></div>`}
function cardHangarActions(v){const id=esc(v.id),isOwned=owned.has(key(v)),isWished=wished.has(key(v));return `<div class="card-hangar-actions"><button type="button" class="card-hangar-btn owned ${isOwned?'active':''}" data-card-owned="${id}" aria-label="${isOwned?'Retirer de Mes vaisseaux':'Ajouter à Mes vaisseaux'}" title="Mes vaisseaux" aria-pressed="${isOwned}">${isOwned?'✓':'＋'}</button><button type="button" class="card-hangar-btn wishlist ${isWished?'active':''}" data-card-wish="${id}" aria-label="${isWished?'Retirer de la Wishlist':'Ajouter à la Wishlist'}" title="Wishlist" aria-pressed="${isWished}">${isWished?'★':'☆'}</button></div>`}
vehicleCard=function(v){const name=human(v.name)||'Vaisseau',u=imageOf(v),img=u?`<img loading="lazy" src="${esc(u)}" referrerpolicy="no-referrer" alt="${esc(name)}" onerror="this.onerror=null;this.replaceWith(Object.assign(document.createElement('div'),{className:'image-fallback ship-fallback',innerHTML:'<strong>${esc(name)}</strong><small>Image en attente</small>'}))">`:fallbackImage(name);const ground=Number(v.is_ground_vehicle)===1;const rawStatus=effectiveStatus(v),st=statusLabel(rawStatus);return `<article class="ship-card" data-vehicle-id="${esc(v.id)}" tabindex="0"><div class="ship-state"><span class="status-badge ${statusClass(rawStatus)}">${esc(st)}</span></div>${cardHangarActions(v)}<div class="ship-image">${img}</div><div class="card-body"><div class="card-kicker"><button class="text-link manufacturer-link" data-manufacturer="${esc(human(v.manufacturer))}">${esc(human(v.manufacturer)||'Constructeur inconnu')}</button><span>${ground?'Terrestre':'Vaisseau'}</span></div><h3>${esc(name)}</h3><div class="card-meta"><div><span>Statut</span><strong>${esc(st)}</strong></div><div><span>Meilleur prix</span><strong class="price">${Number(v.price_min)>0?price(v.price_min):'—'}</strong></div><div><span>Achat en jeu</span><strong>${esc(inGamePurchase(v))}</strong></div><div><span>Boutique RSI</span><strong>${esc(pledgePurchase(v))}</strong></div><div><span>SCU</span><strong>${esc(human(v.scu)||'—')}</strong></div><div><span>Équipage</span><strong>${esc(human(v.crew)||'—')}</strong></div></div></div></article>`}
const catalogBindCards=bindCards;bindCards=function(root=document){catalogBindCards(root);root.querySelectorAll('[data-card-owned]').forEach(b=>b.addEventListener('click',e=>{e.stopPropagation();setHangar(b.dataset.cardOwned,'owned')}));root.querySelectorAll('[data-card-wish]').forEach(b=>b.addEventListener('click',e=>{e.stopPropagation();setHangar(b.dataset.cardWish,'wish')}))}
const oldRenderVehicles=renderVehicles;renderVehicles=function(){oldRenderVehicles();}
function offersFor(v){if(!state.db||v.catalog_only)return[];try{return query(`SELECT o.price_buy,${locationExpr('t')} location FROM vehicle_offers o JOIN vehicles v ON v.id=o.vehicle_id JOIN terminals t ON t.id=o.terminal_id WHERE o.vehicle_id=? AND o.price_buy>0 ORDER BY o.price_buy ASC`,[v.id])}catch{return[]}}
function plainText(v){const doc=new DOMParser().parseFromString(`<body>${human(v)}</body>`,'text/html');return doc.body.textContent?.trim()||''}
function meters(v){const n=Number(v);return Number.isFinite(n)&&n>0?`${n.toLocaleString('fr-FR',{maximumFractionDigits:2})} m`:''}
function massLabel(v){const n=Number(v);return Number.isFinite(n)&&n>0?`${n.toLocaleString('fr-FR',{maximumFractionDigits:0})} kg`:''}
function crewLabel(v){const min=human(v.crew_min),max=human(v.crew);if(min&&max&&min!==max)return`${min} à ${max}`;return max||min||'Non renseigné'}
openVehicle=function(id){
 const detail=state.vehicles.find(v=>String(v.id)===String(id));if(!detail)return;
 const offers=offersFor(detail),ground=Number(detail.is_ground_vehicle)===1,u=imageOf(detail),rawStatus=effectiveStatus(detail),st=statusLabel(rawStatus),name=human(detail.name_full)||human(detail.name)||'Vaisseau';
 const image=u?`<div class="detail-vehicle-image"><img src="${esc(u)}" alt="${esc(name)}" referrerpolicy="no-referrer"></div>`:`<div class="detail-vehicle-image">${fallbackImage(name)}</div>`;
 const fields=[['Statut RSI',st],['Disponibilité',availability(detail)],['Achat en jeu',inGamePurchase(detail)],['Boutique RSI',pledgePurchase(detail)],['Type',ground?'Véhicule terrestre':'Vaisseau'],['Constructeur',human(detail.manufacturer)],['Taille RSI',human(detail.catalog_size)||'Non renseignée'],['Rôle',human(detail.roles)||'Non renseigné'],['SCU',human(detail.scu)||'—'],['Équipage',crewLabel(detail)],['Longueur',meters(detail.catalog_length)],['Largeur',meters(detail.catalog_beam)],['Hauteur',meters(detail.catalog_height)],['Masse',massLabel(detail.catalog_mass)]].filter(x=>x[1]!==null&&x[1]!==undefined&&String(x[1])!=='');
 const purchaseText=offers.length?`<table class="shops"><thead><tr><th>Lieu</th><th>Prix</th></tr></thead><tbody>${offers.map(o=>`<tr><td>${esc(o.location||'—')}</td><td>${price(o.price_buy)}</td></tr>`).join('')}</tbody></table>`:`<div class="empty compact-empty">Aucune offre d’achat en jeu n’est actuellement référencée.</div>`;
 const rsiLinks=`<p class="rsi-source">${human(detail.rsi_url)?`<a href="${esc(human(detail.rsi_url))}" target="_blank" rel="noopener">Voir la fiche RSI ↗</a>`:''}${human(detail.store_url)?`<a href="${esc(human(detail.store_url))}" target="_blank" rel="noopener">Acheter sur RSI ↗</a>`:''}</p>`;
 openDetail(`${image}<div class="detail-head"><p class="eyebrow">FICHE ${ground?'VÉHICULE':'VAISSEAU'}</p><div class="detail-title-row"><h2>${esc(name)}</h2></div><p class="detail-sub"><button class="text-link" data-manufacturer="${esc(human(detail.manufacturer))}">${esc(human(detail.manufacturer))}</button>${human(detail.roles)?' · '+esc(human(detail.roles)):''}</p><div class="hangar-actions"><button class="detail-fav ${owned.has(key(detail))?'active':''}" data-hangar-owned="${esc(detail.id)}">${owned.has(key(detail))?'✓ Dans mes vaisseaux':'＋ Ajouter à mes vaisseaux'}</button><button class="detail-fav ${wished.has(key(detail))?'active':''}" data-hangar-wish="${esc(detail.id)}">${wished.has(key(detail))?'★ Dans la Wishlist':'☆ Ajouter à la Wishlist'}</button></div></div><div class="detail-grid">${fields.map(([k,v])=>`<div class="detail-stat"><span>${esc(k)}</span><strong>${esc(v)}</strong></div>`).join('')}</div>${human(detail.catalog_description)?`<div class="ship-description">${esc(plainText(detail.catalog_description))}</div>`:''}${patchImpact(detail)}<h3>Où acheter en jeu</h3>${purchaseText}${rsiLinks}`);
 document.querySelector('.detail-vehicle-image img')?.addEventListener('error',e=>{e.currentTarget.parentElement.innerHTML=fallbackImage(name)},{once:true});
 document.querySelector('[data-hangar-owned]')?.addEventListener('click',e=>{setHangar(e.currentTarget.dataset.hangarOwned,'owned');openVehicle(id)});
 document.querySelector('[data-hangar-wish]')?.addEventListener('click',e=>{setHangar(e.currentTarget.dataset.hangarWish,'wish');openVehicle(id)});
}
renderHangar=function(){const list=state.vehicles.filter(v=>hangarMode==='owned'?owned.has(key(v)):wished.has(key(v)));$('#hangarCount').textContent=`${list.length} vaisseau${list.length>1?'x':''}`;$('#hangarGrid').innerHTML=list.length?list.map(vehicleCard).join(''):`<div class="empty">${hangarMode==='owned'?'Aucun vaisseau enregistré dans Mes vaisseaux.':'Ta Wishlist est vide.'}</div>`;bindCards($('#hangarGrid'))}
function bindHangarTabs(){document.querySelectorAll('[data-hangar-level]').forEach(b=>b.addEventListener('click',()=>{hangarMode=b.dataset.hangarLevel;document.querySelectorAll('[data-hangar-level]').forEach(x=>x.classList.toggle('active',x===b));renderHangar()}))}
async function loadCatalog(){try{
 const r=await fetch('/api/ships',{headers:{Accept:'application/json'},cache:'no-store'});if(!r.ok)throw 0;
 const data=await r.json();if(!data.ok||!data.items?.length)throw 0;
 const local=state.vehicles.filter(v=>!NON_HULL_ENTRIES.has(catalogKey(v)));
 const byName=new Map();for(const v of local){const k=catalogMatchKey(normalizedName(v));if(k&&!byName.has(k))byName.set(k,v)}
 const merged=[],seen=new Set();
 for(const c of data.items){
  const cname=human(c.name),normalized=normName(cname),matchKey=catalogMatchKey(cname);
  if(!cname||!matchKey||NON_HULL_ENTRIES.has(normalized)||seen.has(matchKey))continue;
  seen.add(matchKey);
  const v=byName.get(matchKey),status=human(c.status),manufacturer=human(c.manufacturer);
  if(v){
   Object.assign(v,{name:cname,name_full:cname,manufacturer:manufacturer||human(v.manufacturer),production_status:status,in_game:c.in_game===true,is_concept:/concept/i.test(status)?1:0,catalog_type:human(c.type),catalog_size:human(c.size),catalog_length:human(c.length)||human(v.catalog_length),catalog_beam:human(c.beam),catalog_height:human(c.height),catalog_mass:human(c.mass),catalog_description:human(c.description),catalog_image:human(c.image)||human(v.url_photo),rsi_url:human(c.rsi_url),store_url:human(c.store_url),pledge_available:c.pledge_available===true?true:c.pledge_available===false?false:null,roles:human(c.focus)||human(v.roles),scu:c.scu??v.scu,crew_min:c.crew_min,crew:c.crew_max??v.crew,msrp:c.msrp});
   merged.push(v);
  }else{
   merged.push({id:`rsi-${human(c.rsi_id)||matchKey}`,name:cname,name_full:cname,manufacturer,production_status:status,in_game:c.in_game===true,is_concept:/concept/i.test(status)?1:0,catalog_type:human(c.type),catalog_size:human(c.size),catalog_length:human(c.length),catalog_beam:human(c.beam),catalog_height:human(c.height),catalog_mass:human(c.mass),catalog_description:human(c.description),catalog_image:human(c.image),rsi_url:human(c.rsi_url),store_url:human(c.store_url),pledge_available:c.pledge_available===true?true:c.pledge_available===false?false:null,roles:human(c.focus),scu:c.scu,crew_min:c.crew_min,crew:c.crew_max,msrp:c.msrp,is_ground_vehicle:human(c.size).toLowerCase()==='vehicle'||human(c.type).toLowerCase()==='ground'?1:0,price_min:null,location:'',catalog_only:true});
  }
 }
 state.vehicles=merged.sort((a,b)=>human(a.name).localeCompare(human(b.name),'fr',{numeric:true}));
 state.manufacturers=[...new Set([...state.manufacturers.map(x=>human(x.name)),...state.vehicles.map(v=>human(v.manufacturer)).filter(Boolean)])].sort((a,b)=>a.localeCompare(b)).map(name=>({name,n:state.vehicles.filter(v=>human(v.manufacturer)===name).length+state.items.filter(v=>human(v.manufacturer)===name).length}));
 setOptions($('#vehicleManufacturer'),state.manufacturers.map(x=>x.name),'Tous les constructeurs');$('#statVehicles').textContent=state.vehicles.length;renderVehicles();ready=true;
}catch(e){console.warn('Catalogue complet indisponible',e)}}
function wait(){if(state.db){bindHangarTabs();loadCatalog()}else setTimeout(wait,150)}wait();
})();
