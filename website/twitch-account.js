(()=>{
  'use strict';
  const adapter=window.AsteriaxHangar;if(!adapter)return;

  const panel=document.createElement('section');panel.className='ax-account';panel.dataset.i18nSkip='';
  panel.innerHTML='<div class="ax-account-copy"><strong id="axAccountTitle"></strong><p id="axAccountStatus" role="status"></p></div><div class="ax-account-actions"><button id="axImport" type="button" hidden></button><button id="axLogout" type="button" hidden></button></div>';
  document.querySelector('#hangar .hangar-tabs')?.before(panel);
  const title=panel.querySelector('#axAccountTitle'),status=panel.querySelector('#axAccountStatus'),importButton=panel.querySelector('#axImport'),logout=panel.querySelector('#axLogout');

  const headerActions=document.createElement('div');headerActions.className='ax-header-actions';headerActions.dataset.i18nSkip='';
  const stream=document.createElement('a');stream.className='ax-stream-state offline';stream.href='https://www.twitch.tv/asteriaxttv';stream.target='_blank';stream.rel='noopener noreferrer';stream.innerHTML='<span class="ax-stream-dot" aria-hidden="true"></span><span class="ax-stream-label">HORS LIGNE</span>';
  const streamLabel=stream.querySelector('.ax-stream-label');
  const login=document.createElement('a');login.id='axLogin';login.className='ax-top-login';login.href='/api/twitch/login';login.hidden=true;
  const topUser=document.createElement('span');topUser.className='ax-top-user';topUser.hidden=true;
  const topLogout=document.createElement('button');topLogout.type='button';topLogout.className='ax-top-logout';topLogout.hidden=true;
  headerActions.append(stream,login,topUser,topLogout);document.querySelector('.nav')?.insertAdjacentElement('afterend',headerActions);
  const adoptLanguageToggle=()=>{const toggle=document.querySelector('.language-toggle');if(toggle&&toggle.parentElement!==headerActions)headerActions.insertBefore(toggle,login)};

  const read=(key,fallback)=>{try{return JSON.parse(localStorage.getItem(key))??fallback}catch{return fallback}};
  const write=(key,value)=>{try{localStorage.setItem(key,JSON.stringify(value));return true}catch{return false}};
  const validSnapshot=s=>({owned:Array.isArray(s?.owned)?s.owned.map(String):[],wishlist:Array.isArray(s?.wishlist)?s.wishlist.map(String):[]});
  let user=null,queue={},busy=false,checking=false,editable=false,configured=false,message='checking';
  let streamKnown=false,streamIsLive=false,streamTitle='';
  let owner=read('ax_hangar_account',null),guest=validSnapshot(read('ax_hangar_guest',null));
  const english=()=>window.AsteriaxI18n?.isEnglish?.()===true;
  const words={checking:['Vérification de la connexion…','Checking connection…'],guest:['Sauvegarde sur cet appareil. Connecte-toi pour retrouver ton hangar partout.','Saved on this device. Sign in to access your hangar everywhere.'],setup:['Connexion Twitch en préparation. Ton hangar local reste disponible.','Twitch sign-in is being set up. Your local hangar remains available.'],saved:['Hangar synchronisé. Actualisation automatique entre tes appareils.','Hangar synced. Changes refresh automatically across your devices.'],pending:['Modifications en attente de synchronisation.','Changes waiting to sync.'],error:['Connexion indisponible. Tes données sont conservées ; réessaie dans un instant.','Connection unavailable. Your data is preserved; please try again shortly.'],expired:['Session expirée. Reconnecte-toi à Twitch pour synchroniser tes modifications.','Session expired. Sign in with Twitch again to sync your changes.'],imported:['Vaisseaux de cet appareil importés, sans remplacer ceux du compte.','Device ships imported without replacing your account entries.']};

  function paint(){
    const en=english();
    title.textContent=user?(en?'Connected as ':'Connecté : ')+user.login:(en?'Your hangar, everywhere':'Ton hangar, partout');
    status.textContent=(words[message]||words.error)[en?1:0];
    login.textContent=en?'Sign in with Twitch':'Connexion Twitch';login.setAttribute('aria-label',en?'Sign in with Twitch':'Se connecter avec Twitch');
    logout.textContent=en?'Sign out':'Se déconnecter';topLogout.textContent=en?'Sign out':'Déconnexion';
    importButton.textContent=en?'Import this device’s ships':'Importer les vaisseaux de cet appareil';
    login.hidden=!!user||!configured;logout.hidden=!user;topUser.hidden=!user;topLogout.hidden=!user;
    topUser.textContent=user?user.login:'';topUser.title=user?user.login:'';
    logout.disabled=busy;topLogout.disabled=busy;importButton.hidden=!user||!(guest.owned.length+guest.wishlist.length);importButton.disabled=busy;
    stream.classList.toggle('live',streamIsLive);stream.classList.toggle('offline',!streamIsLive);
    streamLabel.textContent=streamIsLive?(en?'ONLINE':'EN LIGNE'):(en?'OFFLINE':'HORS LIGNE');
    stream.setAttribute('aria-label',streamIsLive?(en?'AsteriaxTTV is online on Twitch':'AsteriaxTTV est en ligne sur Twitch'):(en?'AsteriaxTTV is offline on Twitch':'AsteriaxTTV est hors ligne sur Twitch'));
    stream.title=streamIsLive&&streamTitle?streamTitle:(streamIsLive?'AsteriaxTTV · en ligne':'AsteriaxTTV · hors ligne');
  }

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
      const owned=new Set(snapshot.owned),wishlist=new Set(snapshot.wishlist);for(const op of Object.values(queue)){owned.delete(op.shipId);wishlist.delete(op.shipId);if(op.status==='owned')owned.add(op.shipId);if(op.status==='wishlist')wishlist.add(op.shipId)}
      apply({owned:[...owned],wishlist:[...wishlist]});owner=user.id;write('ax_hangar_account',owner);
    }
    editable=true;await flush();
  }catch(error){configured=error.data?.configured!==false;message=error.data?.configured===false?'setup':'error';editable=!owner&&!user}finally{checking=false;paint()}}

  window.AsteriaxAccount={canEdit:()=>editable&&!checking&&!busy};
  document.addEventListener('asteriax:hangar-edit',event=>{if(!user)return;const {shipId,status:state}=event.detail;queue[shipId]={shipId,status:state,mutationId:crypto.randomUUID()};persist();message='pending';paint();void flush()});

  importButton.addEventListener('click',async()=>{if(!user||busy)return;busy=true;paint();try{
    const entries=new Map(guest.wishlist.map(id=>[id,'wishlist']));guest.owned.forEach(id=>entries.set(id,'owned'));const ops=[...entries].map(([shipId,status])=>({shipId,status,mutationId:crypto.randomUUID()}));
    for(let i=0;i<ops.length;i+=20)await api('/api/hangar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({userId:user.id,mode:'import',operations:ops.slice(i,i+20)})});
    message='imported';
  }catch{message='error'}finally{busy=false;await flush();paint()}});

  async function signOut(){if(busy||!user)return;if(Object.keys(queue).length){message='pending';paint();await flush();if(Object.keys(queue).length)return}busy=true;paint();try{await api('/api/twitch/logout',{method:'POST'});user=null;owner=null;queue={};write('ax_hangar_account',null);apply(guest);editable=true;message='guest'}catch{message='error'}finally{busy=false;paint()}}
  logout.addEventListener('click',signOut);topLogout.addEventListener('click',signOut);

  async function refreshLive(){try{const data=await api('/api/twitch/live');const age=Date.now()-Date.parse(data.checkedAt);streamKnown=typeof data.live==='boolean'&&age>=0&&age<180000;streamIsLive=streamKnown&&data.live===true;streamTitle=typeof data.title==='string'?data.title:''}catch{streamKnown=false;streamIsLive=false;streamTitle=''}finally{paint()}}

  document.addEventListener('asteriax:language-change',()=>{adoptLanguageToggle();paint()});
  document.addEventListener('visibilitychange',()=>{if(!document.hidden){void refresh();void refreshLive()}});
  window.addEventListener('online',()=>{void refresh();void refreshLive()});
  setInterval(()=>{if(!document.hidden){void refresh();void refreshLive()}},60000);
  const url=new URL(location.href);if(url.searchParams.has('twitch')){url.searchParams.delete('twitch');history.replaceState(null,'',url.pathname+url.search+url.hash)}
  paint();void refresh();void refreshLive();
})();