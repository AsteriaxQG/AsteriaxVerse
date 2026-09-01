(()=>{
  const grid=document.querySelector('#newsFeed');
  const status=document.querySelector('#newsStatus');
  if(!grid)return;
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const labels={'PATCH':'PATCH','ROADMAP':'ROADMAP','SNEAK PEEK':'SNEAK PEEK','VIDEO':'VIDÉO','KNOWN ISSUE':'KNOWN ISSUE','NEWS':'ACTU'};
  function card(x,i){return `<a class="news-card ${i===0?'featured':''}" href="${esc(x.url)}" target="_blank" rel="noopener"><span>${esc(labels[x.category]||x.category||'ACTU')}</span><h3>${esc(x.title)}</h3><p>Source officielle Roberts Space Industries.</p><strong>Lire sur RSI ↗</strong></a>`}
  async function load(){
    status.textContent='Mise à jour des actualités…';
    try{
      const res=await fetch('/api/news',{headers:{Accept:'application/json'}});
      if(!res.ok)throw new Error('API indisponible');
      const data=await res.json();
      if(!data.ok||!data.items?.length)throw new Error('Aucune actualité');
      grid.innerHTML=data.items.map(card).join('');
      const d=new Date(data.updatedAt);
      status.textContent=`Automatique · ${data.items.length} actualités · vérifié ${d.toLocaleString('fr-FR')}`;
    }catch(e){
      grid.innerHTML=`<a class="news-card featured" href="https://robertsspaceindustries.com/en/patch-notes" target="_blank" rel="noopener"><span>PATCH</span><h3>Patch notes officielles</h3><p>Le flux automatique est temporairement indisponible.</p><strong>Ouvrir RSI ↗</strong></a><a class="news-card" href="https://robertsspaceindustries.com/en/comm-link/transmission/star-citizen" target="_blank" rel="noopener"><span>ACTUS</span><h3>Comm-Link Star Citizen</h3><p>Accède directement aux dernières publications officielles.</p><strong>Ouvrir RSI ↗</strong></a>`;
      status.textContent='Flux automatique temporairement indisponible';
    }
  }
  load();
  document.querySelectorAll('.nav-btn[data-view="news"]').forEach(b=>b.addEventListener('click',()=>{if(!grid.dataset.refreshed){grid.dataset.refreshed='1';setTimeout(load,50)}}));
})();
