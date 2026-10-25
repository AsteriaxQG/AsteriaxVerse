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
    const stage=dialog.querySelector('.iae-lightbox-stage');
    const image=dialog.querySelector('img');
    const level=dialog.querySelector('[data-iae-zoom-level]');
    const pointers=new Map();
    let scale=1,panX=0,panY=0,lastPoint=null,pinch=null;
    function paint(){
      if(scale===1){panX=0;panY=0}
      else if(stage&&image){
        const maxX=Math.max(0,(image.clientWidth*scale-stage.clientWidth)/2);
        const maxY=Math.max(0,(image.clientHeight*scale-stage.clientHeight)/2);
        panX=Math.max(-maxX,Math.min(maxX,panX));
        panY=Math.max(-maxY,Math.min(maxY,panY));
      }
      if(image)image.style.transform=`translate(${panX}px,${panY}px) scale(${scale})`;
      if(level)level.textContent=`${Math.round(scale*100)} %`;
    }
    function zoom(value){scale=Math.max(1,Math.min(5,value));paint()}
    dialog.querySelector('[data-iae-zoom-in]')?.addEventListener('click',()=>zoom(scale*1.5));
    dialog.querySelector('[data-iae-zoom-out]')?.addEventListener('click',()=>zoom(scale/1.5));
    dialog.querySelector('[data-iae-zoom-reset]')?.addEventListener('click',()=>zoom(1));
    stage?.addEventListener('wheel',event=>{event.preventDefault();zoom(scale*(event.deltaY<0?1.2:1/1.2))},{passive:false});
    stage?.addEventListener('dblclick',()=>zoom(scale===1?2:1));
    stage?.addEventListener('pointerdown',event=>{
      pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});
      stage.setPointerCapture(event.pointerId);
      if(pointers.size===1)lastPoint={x:event.clientX,y:event.clientY};
      if(pointers.size===2){const [a,b]=[...pointers.values()];pinch={distance:Math.hypot(a.x-b.x,a.y-b.y),scale}}
      if(scale>1)stage.classList.add('is-dragging');
    });
    stage?.addEventListener('pointermove',event=>{
      if(!pointers.has(event.pointerId))return;
      pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});
      if(pointers.size===2&&pinch){
        const [a,b]=[...pointers.values()];
        zoom(pinch.scale*Math.hypot(a.x-b.x,a.y-b.y)/Math.max(1,pinch.distance));
      }else if(scale>1&&lastPoint){
        panX+=event.clientX-lastPoint.x;panY+=event.clientY-lastPoint.y;
        lastPoint={x:event.clientX,y:event.clientY};paint();
      }
    });
    function release(event){
      pointers.delete(event.pointerId);pinch=null;
      lastPoint=pointers.size===1?[...pointers.values()][0]:null;
      if(!pointers.size)stage.classList.remove('is-dragging');
    }
    stage?.addEventListener('pointerup',release);
    stage?.addEventListener('pointercancel',release);
    document.addEventListener('click',event=>{
      const link=event.target.closest?.('#iae a[data-iae-image]');
      if(link){
        event.preventDefault();
        image.src=link.href;
        image.alt=link.querySelector('img')?.alt||'IAE';
        zoom(1);
        dialog.showModal();
      }
    });
    dialog.querySelector('.iae-lightbox-close')?.addEventListener('click',()=>dialog.close());
    dialog.addEventListener('click',event=>{if(event.target===dialog)dialog.close()});
  }
  if(location.hash==='#iae')load();
})();
