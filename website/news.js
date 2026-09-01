(()=>{
  const section=document.querySelector('#news');
  const grid=document.querySelector('#newsFeed');
  const status=document.querySelector('#newsStatus');
  const filters=[...document.querySelectorAll('[data-news-filter]')];
  if(!section||!grid||!status)return;
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const labels={'PATCH':'PATCH','ROADMAP':'ROADMAP','SNEAK PEEK':'SNEAK PEEK','VIDEO':'VIDÉO','KNOWN ISSUE':'KNOWN ISSUE','NEWS':'ACTU'};
  let items=[],active='ALL',loading=false,lastLoaded=0;
  function card(x,i){const meta=[x.posted,x.excerpt].filter(Boolean).join(' · ');return `<a class="news-card ${i===0?'featured':''}" data-category="${esc(x.category||'NEWS')}" href="${esc(x.url)}" target="_blank" rel="noopener"><span>${esc(labels[x.category]||x.category||'ACTU')}</span><h3>${esc(x.title)}</h3><p>${esc(meta||'Source officielle Roberts Space Industries.')}</p><strong>Lire sur RSI ↗</strong></a>`}
  function render(){const list=active==='ALL'?items:items.filter(x=>x.category===active);grid.innerHTML=list.length?list.map(card).join(''):`<div class="empty">Aucune publication dans cette catégorie pour le moment.</div>`;filters.forEach(b=>b.classList.toggle('active',b.dataset.newsFilter===active));}
  async function load(force=false){if(loading)return;if(!force&&Date.now()-lastLoaded<120000&&items.length)return;loading=true;status.textContent='Mise à jour automatique…';try{const url='/api/news?ts='+Date.now();const res=await fetch(url,{headers:{Accept:'application/json'},cache:'no-store'});if(!res.ok)throw new Error('API indisponible');const data=await res.json();if(!data.ok||!data.items?.length)throw new Error('Aucune actualité');items=data.items;lastLoaded=Date.now();render();const d=new Date(data.updatedAt);status.textContent=`Automatique · ${items.length} publications · vérifié ${d.toLocaleString('fr-FR')}${data.live===false?' · mode secours':''}`;}catch(e){grid.innerHTML=`<a class="news-card featured" href="https://robertsspaceindustries.com/en/patch-notes" target="_blank" rel="noopener"><span>PATCH</span><h3>Patch notes officielles</h3><p>Le flux automatique est temporairement indisponible.</p><strong>Ouvrir RSI ↗</strong></a><a class="news-card" href="https://robertsspaceindustries.com/en/comm-link" target="_blank" rel="noopener"><span>ACTU</span><h3>Comm-Link Star Citizen</h3><p>Accède directement aux dernières publications officielles.</p><strong>Ouvrir RSI ↗</strong></a>`;status.textContent='Flux automatique temporairement indisponible';}finally{loading=false}}
  filters.forEach(b=>b.addEventListener('click',()=>{active=b.dataset.newsFilter;render()}));
  load(true);
  document.querySelectorAll('.nav-btn[data-view="news"],[data-go="news"]').forEach(b=>b.addEventListener('click',()=>setTimeout(()=>load(true),80)));
})();