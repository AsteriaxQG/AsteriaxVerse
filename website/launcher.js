(()=>{
  const version=document.querySelector('#homeLauncherVersion'),date=document.querySelector('#homeLauncherDate'),link=document.querySelector('#homeLauncherLink');
  if(!version||!date||!link)return;
  let data=null,busy=false,failed=false;
  const en=()=>window.AsteriaxI18n?.isEnglish?.()===true;
  function render(){
    const english=en();
    version.textContent=data?.version?'v'+data.version:failed?(english?'Version unavailable':'Version indisponible'):(english?'Checking version…':'Vérification de la version…');
    link.textContent=english?'View RSI Launcher ↗':'Voir le RSI Launcher ↗';
    date.hidden=!data?.version;
    if(data?.version){
      const value=data.stale?data.checkedAt:data.publishedAt;
      const parsed=new Date(value||'');
      date.textContent=Number.isFinite(parsed.getTime())?(data.stale?(english?'Last verified on ':'Dernière vérification le '):(english?'Released on ':'Publié le '))+parsed.toLocaleDateString(english?'en-GB':'fr-FR',{day:'numeric',month:'long',year:'numeric'}):(english?'Stable release':'Version stable');
      if(Number.isFinite(parsed.getTime()))date.dateTime=parsed.toISOString();else date.removeAttribute('datetime');
    }
  }
  async function refresh(){
    if(busy)return;busy=true;
    try{const payload=await window.AsteriaxApi.getJson('/api/launcher',{ttlMs:300000});if(!payload.ok||!/^\d+\.\d+\.\d+$/.test(payload.version))throw Error();data=payload;failed=false}
    catch{failed=true;if(data)data={...data,stale:true}}
    finally{busy=false;render()}
  }
  document.addEventListener('asteriax:language-change',render);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)void refresh()});
  setInterval(()=>{if(!document.hidden)void refresh()},300000);
  render();void refresh();
})();
