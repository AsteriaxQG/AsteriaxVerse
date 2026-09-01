(()=>{
  const section=document.querySelector('#news');
  const grid=document.querySelector('#newsFeed');
  const status=document.querySelector('#newsStatus');
  const refresh=document.querySelector('#refreshNews');
  const filters=[...document.querySelectorAll('[data-news-filter]')];
  if(!section||!grid||!status)return;
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const labels={'PATCH':'PATCH','ROADMAP':'ROADMAP','SNEAK PEEK':'SNEAK PEEK','VIDEO':'VIDÉO','KNOWN ISSUE':'KNOWN ISSUE','NEWS':'POST'};
  let items=[],active='ALL',loading=false,lastLoaded=0,autoRefreshTimer=0;

  function postedLabel(value=''){
    return value.replace(/(\d+|an?|one) minute(s?) ago/i,'il y a $1 minute$2').replace(/(\d+|an?|one) hour(s?) ago/i,'il y a $1 heure$2').replace(/(\d+|an?|one) day(s?) ago/i,'il y a $1 jour$2').replace(/(\d+|an?|one) week(s?) ago/i,'il y a $1 semaine$2').replace(/\bone\b/gi,'1').replace(/\ban?\b/gi,'1');
  }
  function card(x){
    const image=x.image?`<div class="news-image"><img loading="lazy" src="${esc(x.image)}" alt="" referrerpolicy="no-referrer"></div>`:'<div class="news-image news-image-fallback"><span>ASTERIAXVERSE</span></div>';
    return `<a class="news-card" data-category="${esc(x.category||'NEWS')}" href="${esc(x.url)}" target="_blank" rel="noopener">${image}<div class="news-card-content"><div class="news-card-meta"><span>${esc(labels[x.category]||x.category||'POST')}</span><time>${esc(postedLabel(x.posted||''))}</time></div><h3>${esc(x.title)}</h3><p>${esc(x.excerpt||'Publication officielle Roberts Space Industries.')}</p><strong>Ouvrir sur RSI ↗</strong></div></a>`;
  }
  function render(){const list=active==='ALL'?items:items.filter(x=>x.category===active);grid.innerHTML=list.length?list.map(card).join(''):`<div class="empty">Aucune publication dans cette catégorie pour le moment.</div>`;filters.forEach(b=>b.classList.toggle('active',b.dataset.newsFilter===active));}
  async function load(force=false){
    if(loading)return;if(!force&&Date.now()-lastLoaded<120000&&items.length)return;
    loading=true;refresh?.classList.add('loading');if(refresh)refresh.disabled=true;status.textContent='Actualisation du flux officiel RSI…';
    try{
      const url=`/api/news?${force?'refresh=1&':''}ts=${Date.now()}`;
      const res=await fetch(url,{headers:{Accept:'application/json'},cache:'no-store'});if(!res.ok)throw new Error('API indisponible');
      const data=await res.json();if(!data.ok||!data.items?.length)throw new Error('Aucune actualité');
      items=data.items;lastLoaded=Date.now();render();
      const d=new Date(data.updatedAt);status.textContent=`${items.length} publications officielles · actualisé ${d.toLocaleString('fr-FR')}${data.live===false?' · mode secours':''}`;
      clearTimeout(autoRefreshTimer);autoRefreshTimer=setTimeout(()=>load(true),Math.max(300,Number(data.refreshSeconds)||300)*1000);
    }catch(e){
      grid.innerHTML=`<a class="news-card" href="https://robertsspaceindustries.com/en/patch-notes" target="_blank" rel="noopener"><div class="news-image news-image-fallback"><span>PATCH NOTES</span></div><div class="news-card-content"><div class="news-card-meta"><span>PATCH</span></div><h3>Patch notes officielles</h3><p>Le flux automatique est temporairement indisponible.</p><strong>Ouvrir RSI ↗</strong></div></a><a class="news-card" href="https://robertsspaceindustries.com/en/comm-link" target="_blank" rel="noopener"><div class="news-image news-image-fallback"><span>COMM-LINK</span></div><div class="news-card-content"><div class="news-card-meta"><span>POST</span></div><h3>Actualités Star Citizen</h3><p>Accède directement aux dernières publications officielles.</p><strong>Ouvrir RSI ↗</strong></div></a>`;
      status.textContent='Flux automatique temporairement indisponible';
    }finally{loading=false;refresh?.classList.remove('loading');if(refresh)refresh.disabled=false}
  }
  filters.forEach(b=>b.addEventListener('click',()=>{active=b.dataset.newsFilter;render()}));
  refresh?.addEventListener('click',()=>load(true));
  document.querySelectorAll('.nav-btn[data-view="news"],[data-go="news"]').forEach(b=>b.addEventListener('click',()=>setTimeout(()=>load(false),80)));
  load(false);
})();
