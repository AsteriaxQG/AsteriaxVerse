(()=>{
  const q=s=>document.querySelector(s);
  const fr=()=>!window.AsteriaxI18n?.isEnglish?.();
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const official=url=>{try{const u=new URL(url);return u.protocol==='https:'&&/(^|\.)robertsspaceindustries\.com$/.test(u.hostname)?u.href:''}catch{return''}};
  let articles=[],loaded=false;
  function render(){
    const grid=q('#iaeNewsGrid'),status=q('#iaeNewsStatus');if(!grid||!status)return;
    status.textContent=articles.length?(fr()?'${count} annonce(s) officielle(s)'.replace('${count}',articles.length):'${count} official announcement(s)'.replace('${count}',articles.length)):(fr()?'De plus amples informations à venir.':'More information coming soon.');
    grid.innerHTML=articles.map(a=>'<a class="iae-news-card" href="'+esc(a.link)+'" target="_blank" rel="noopener noreferrer"><time>'+esc(a.date)+'</time><h3>'+esc(a.title)+'</h3><p>'+esc(a.excerpt||'Roberts Space Industries')+'</p></a>').join('');
  }
  async function load(){
    try{
      const data=await window.AsteriaxApi.getJson('/api/news',{ttlMs:120000});
      articles=(data.items||[]).filter(a=>/\bIAE\b|Intergalactic Aerospace Expo/i.test(a.title+' '+(a.excerpt||''))).filter(a=>/2026/.test(a.publishedAt||a.posted||'')||/2956/.test(a.title||'')).map(a=>({title:a.title,excerpt:a.excerpt,date:a.posted||'',link:official(a.url)})).filter(a=>a.link).slice(0,6);
    }catch{articles=[]}loaded=true;render();
  }
  document.addEventListener('asteriax:language-change',render);
  document.addEventListener('asteriax:view-change',event=>{if(event.detail==='iae'&&!loaded)load()});
  const dialog=q('#iaeImageDialog');
  if(dialog){
    document.addEventListener('click',event=>{
      const link=event.target.closest?.('#iae a[data-iae-image]');
      if(link){
        event.preventDefault();
        const image=q('#iaeImageDialog img');
        image.src=link.href;
        image.alt=link.querySelector('img')?.alt||'IAE';
        dialog.showModal();
      }
    });
    dialog.querySelector('.iae-lightbox-close')?.addEventListener('click',()=>dialog.close());
    dialog.addEventListener('click',event=>{if(event.target===dialog)dialog.close()});
  }
  if(location.hash==='#iae')load();
})();
