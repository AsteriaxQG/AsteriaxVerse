(()=>{
  'use strict';
  const adapter=window.AsteriaxHangar;if(!adapter)return;
  const panel=document.createElement('section');panel.className='ax-account';panel.dataset.i18nSkip='';
  panel.innerHTML='<div class="ax-account-copy"><strong id="axAccountTitle"></strong><p id="axAccountStatus" role="status"></p></div><div class="ax-account-actions"><a id="axLogin" href="/api/twitch/login" hidden></a><button id="axImport" type="button" hidden></button><button id="axLogout" type="button" hidden></button></div>';
  document.querySelector('#hangar .hangar-tabs')?.before(panel);
  const title=panel.querySelector('#axAccountTitle'),status=panel.querySelector('#axAccountStatus'),login=panel.querySelector('#axLogin'),importButton=panel.querySelector('#axImport'),logout=panel.querySelector('#axLogout');
  const live=document.createElement('a');live.className='ax-live-strip';live.href='https://www.twitch.tv/asteriaxttv';live.target='_blank';live.rel='noopener noreferrer';live.hidden=true;live.dataset.i18nSkip='';live.innerHTML='<span class="ax-live-dot" aria-hidden="true"></span><span></span>';document.querySelector('.topbar')?.after(live);
  const read=(key,fallback)=>{try{return JSON.parse(localStorage.getItem(key))??fallback}catch{return fallback}};
  const write=(key,value)=>{try{localStorage.setItem(key,JSON.stringify(value));return true}catch{return false}};
  const validSnapshot=s=>({owned:Array.isArray(s?.owned)?s.owned.map(String):[],wishlist:Array.isArray(s?.wishlist)?s.wishlist.map(String):[]});
  let user=null,queue={},busy=false,checking=false,editable=false,configured=false,message='checking';
  let owner=read('ax_hangar_account',null),guest=validSnapshot(read('ax_hangar_guest',null));
  const english=()=>window.AsteriaxI18n?.isEnglish?.()===true;
  const words={checking:['Vérification de la connexion…','Checking connection…'],guest:['Sauvegarde sur cet appareil. Connecte-toi pour retrouver ton hangar partout.','Saved on this device. Sign in to access your hangar everywhere.'],setup:['Connexion Twitch en préparation. Ton hangar local reste disponible.','Twitch sign-in is being set up. Your local hangar remains available.'],saved:['Hangar synchronisé. Actualisation automatique entre tes appareils.','Hangar synced. Changes refresh automatically across your devices.'],pending:['Modifications en attente de synchronisation.','Changes waiting to sync.'],error:['Connexion indisponible. Tes données sont conservées ; réessaie dans un instant.','Connection unavailable. Your data is preserved; please try again shortly.'],expired:['Session expirée. Reconnecte-toi à Twitch pour synchroniser tes modifications.','Session expired. Sign in with Twitch again to sync your changes.'],imported:['Vaisseaux de cet appareil importés, sans remplacer ceux du compte.','Device ships imported without replacing your account entries.']};
  function paint(){const en=english();title.textContent=user?(en?'Connected as ':'Connecté : ')+user.login:(en?'Your hangar, everywhere':'Ton hangar, partout');status.textContent=(words[message]||words.error)[en?1:0];login.textContent=en?'Sign in with Twitch':'Se connecter avec Twitch';logout.textContent=en?'Sign out':'Se déconnecter';importButton.textContent=en?'Import this device’s ships':'Importer les vaisseaux de cet appareil';login.hidden=!!user||!configured;logout.hidden=!user;importButton.hidden=!user||!(guest.owned.length+guest.wishlist.length);logout.disabled=busy;importButton.disabled=busy;live.lastElementChild.textContent=en?'AsteriaxTTV is live · Watch on Twitch ↗':'AsteriaxTTV est en live · Regarder sur Twitch ↗'}
  function apply(snapshot){adapter.replace(validSnapshot(snapshot));document.querySelector('#homeOwnedCount').textContent=snapshot.owned.length;document.querySelector('#homeWishCount').textContent=snapshot.wishlist.length}
  async function api(path,options={}){const r=await fetch(path,{...options,credentials:'same-origin',cache:'no-store',signal:AbortSignal.timeout(12000)});const data=await r.json();if(!r.ok){const err=new Error(data.error||'Unavailable');err.status=r.status;err.data=data;throw err}return data}
  function persist(){write('ax_sync_queue:'+user.id,queue)}
  async function flush(){if(!user||busy||!editable)return;busy=true;paint();try{
    while(Object.keys(queue).length){const batch=Object.values(queue).slice(0,20);message='pending';paint();await api('/api/hangar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({userId:user.id,mode:'set',operations:batch})});for(const op of batch)if(queue[op.shipId]?.mutationId===op.mutationId)delete queue[op.shipId];persist()}
    const snapshot=await api('/api/hangar');if(snapshot.userId!==user.id)throw Error('Account changed');if(!Object.keys(queue).length)apply(snapshot);message='saved';
  }catch(error){message=error.status===401?'expired':'error';if(error.status===401||error.status===409){editable=false;user=null}}finally{busy=false;paint()}}
  async function refresh(){if(checking||busy)return;checking=true;try{
    const auth=await api('/api/twitch/session');configured=auth.configured;
    if(!auth.user){user=null;editable=!owner;message=owner?'expired':'guest';paint();return}
    const first=!user||user.id!==auth.user.id;user=auth.user;
    if(first){
      if(!owner){guest=validSnapshot(adapter.read());write('ax_hangar_guest',guest)}
      queue=read('ax_sync_queue:'+user.id,{});if(!queue||Array.isArray(queue)||typeof queue!=='object')queue={};
      const snapshot=await api('/api/hangar');if(snapshot.userId!==user.id)throw Error('Account changed');
      // Overlay this account's pending edits only; never upload another account's data.
      const owned=new Set(snapshot.owned),wishlist=new Set(snapshot.wishlist);for(const op of Object.values(queue)){owned.delete(op.shipId);wishlist.delete(op.shipId);if(op.status==='owned')owned.add(op.shipId);if(op.status==='wishlist')wishlist.add(op.shipId)}
      apply({owned:[...owned],wishlist:[...wishlist]});owner=user.id;write('ax_hangar_account',owner);
    }
    editable=true;await flush();
  }catch(error){configured=error.data?.configured!==false;message=error.data?.configured===false?'setup':'error';editable=!owner&&!user}finally{checking=false;paint()}}
  window.AsteriaxAccount={canEdit:()=>editable&&!checking&&!busy};
  document.addEventListener('asteriax:hangar-edit',event=>{if(!user){return}const {shipId,status:state}=event.detail;queue[shipId]={shipId,status:state,mutationId:crypto.randomUUID()};persist();message='pending';paint();void flush()});
  importButton.addEventListener('click',async()=>{if(!user||busy)return;busy=true;paint();try{
    const entries=new Map(guest.wishlist.map(id=>[id,'wishlist']));guest.owned.forEach(id=>entries.set(id,'owned'));const ops=[...entries].map(([shipId,status])=>({shipId,status,mutationId:crypto.randomUUID()}));
    for(let i=0;i<ops.length;i+=20)await api('/api/hangar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({userId:user.id,mode:'import',operations:ops.slice(i,i+20)})});
    message='imported';
  }catch{message='error'}finally{busy=false;await flush();paint()}});
  logout.addEventListener('click',async()=>{if(busy||!user)return;if(Object.keys(queue).length){message='pending';paint();await flush();if(Object.keys(queue).length)return}busy=true;paint();try{await api('/api/twitch/logout',{method:'POST'});user=null;owner=null;queue={};write('ax_hangar_account',null);apply(guest);editable=true;message='guest'}catch{message='error'}finally{busy=false;paint()}});
  async function refreshLive(){try{const data=await api('/api/twitch/live');const age=Date.now()-Date.parse(data.checkedAt);live.hidden=!(data.live===true&&age>=0&&age<180000);paint()}catch{live.hidden=true}}
  document.addEventListener('asteriax:language-change',paint);
  document.addEventListener('visibilitychange',()=>{if(document.hidden){live.hidden=true;return}void refresh();void refreshLive()});
  window.addEventListener('online',()=>{void refresh();void refreshLive()});
  setInterval(()=>{if(!document.hidden){void refresh();void refreshLive()}},60000);
  const url=new URL(location.href);if(url.searchParams.has('twitch')){url.searchParams.delete('twitch');history.replaceState(null,'',url.pathname+url.search+url.hash)}
  paint();void refresh();void refreshLive();
})();
