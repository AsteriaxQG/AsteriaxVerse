(()=>{
  'use strict';
  // Twitch live status and the language toggle are independent from account features.
  const headerActions=document.createElement('div');
  headerActions.className='ax-header-actions';
  headerActions.dataset.i18nSkip='';
  const stream=document.createElement('a');
  stream.className='ax-stream-state offline';
  stream.href='https://www.twitch.tv/asteriaxttv';
  stream.target='_blank';
  stream.rel='noopener noreferrer';
  stream.innerHTML='<span class="ax-stream-dot" aria-hidden="true"></span><span class="ax-stream-label">CHAÎNE TWITCH</span>';
  headerActions.append(stream);
  document.querySelector('.nav')?.insertAdjacentElement('afterend',headerActions);

  const streamLabel=stream.querySelector('.ax-stream-label');
  let streamIsLive=false,streamTitle='',streamId='',livePopup=null,popupTimer;
  const english=()=>window.AsteriaxI18n?.isEnglish?.()===true;
  const popupKey=()=>`ax_live_popup_collapsed_${streamId||new Date().toISOString().slice(0,10)}`;

  function collapsePopup(){
    clearTimeout(popupTimer);
    if(streamId||streamIsLive)try{sessionStorage.setItem(popupKey(),'1')}catch{}
    livePopup?.classList.add('is-collapsed');
  }

  function expandPopup(){
    try{sessionStorage.removeItem(popupKey())}catch{}
    livePopup?.classList.remove('is-collapsed');
    clearTimeout(popupTimer);
    popupTimer=setTimeout(collapsePopup,15000);
  }

  function paintPopup(){
    if(!streamIsLive){clearTimeout(popupTimer);livePopup?.remove();livePopup=null;return}
    if(livePopup&&livePopup.dataset.streamId!==streamId){clearTimeout(popupTimer);livePopup.remove();livePopup=null}
    if(!livePopup){
      livePopup=document.createElement('aside');
      livePopup.className='ax-live-popup';
      livePopup.dataset.streamId=streamId;
      livePopup.setAttribute('aria-label','AsteriaxTTV sur Twitch');
      livePopup.innerHTML='<button class="ax-live-popup-reopen" type="button"><span class="ax-stream-dot" aria-hidden="true"></span><span>LIVE</span></button><button class="ax-live-popup-close" type="button" aria-label="Réduire la notification">×</button><span class="ax-live-popup-kicker"><span class="ax-stream-dot" aria-hidden="true"></span><span class="ax-live-popup-status"></span></span><strong class="ax-live-popup-heading"></strong><p class="ax-live-popup-title"></p><a class="ax-live-popup-watch" href="https://www.twitch.tv/asteriaxttv" target="_blank" rel="noopener noreferrer"></a>';
      livePopup.querySelector('.ax-live-popup-close').addEventListener('click',collapsePopup);
      livePopup.querySelector('.ax-live-popup-reopen').addEventListener('click',expandPopup);
      livePopup.querySelector('.ax-live-popup-watch').addEventListener('click',collapsePopup);
      document.body.append(livePopup);
      let collapsed=false;
      try{collapsed=sessionStorage.getItem(popupKey())==='1'}catch{}
      if(collapsed)livePopup.classList.add('is-collapsed');
      else popupTimer=setTimeout(collapsePopup,15000);
    }
    const en=english();
    livePopup.querySelector('.ax-live-popup-status').textContent=en?'LIVE NOW':'EN DIRECT';
    livePopup.querySelector('.ax-live-popup-heading').textContent=en?'AsteriaxTTV is live!':'AsteriaxTTV est en live !';
    const title=livePopup.querySelector('.ax-live-popup-title');
    title.textContent=streamTitle|| (en?'Join the stream on Twitch.':'Rejoins le live sur Twitch.');
    livePopup.querySelector('.ax-live-popup-watch').textContent=en?'Watch the stream ↗':'Voir le live ↗';
    livePopup.querySelector('.ax-live-popup-reopen').setAttribute('aria-label',en?'Open live stream notification':'Ouvrir la notification du direct');
  }

  function adoptLanguageToggle(){
    const toggle=document.querySelector('.language-toggle');
    if(toggle&&toggle.parentElement!==headerActions)headerActions.append(toggle);
  }

  function paint(){
    const en=english();
    stream.classList.toggle('live',streamIsLive);
    stream.classList.toggle('offline',!streamIsLive);
    streamLabel.textContent=streamIsLive?(en?'LIVE ON TWITCH':'EN LIVE SUR TWITCH'):(en?'TWITCH CHANNEL':'CHAÎNE TWITCH');
    stream.setAttribute('aria-label',streamIsLive?(en?'Watch AsteriaxTTV live on Twitch':'Voir AsteriaxTTV en direct sur Twitch'):(en?'Open the AsteriaxTTV Twitch channel':'Ouvrir la chaîne Twitch AsteriaxTTV'));
    stream.title=streamIsLive&&streamTitle?streamTitle:(en?'Open the Twitch channel':'Voir la chaîne Twitch');
    paintPopup();
  }

  async function refreshLive(){
    try{
      const response=await fetch('/api/twitch/live',{cache:'no-store',signal:AbortSignal.timeout(8000)});
      if(!response.ok)throw Error('Unavailable');
      const data=await response.json();
      const age=Date.now()-Date.parse(data.checkedAt);
      streamIsLive=data.live===true&&age>=0&&age<180000;
      streamTitle=typeof data.title==='string'?data.title:'';
      streamId=streamIsLive&&typeof data.streamId==='string'?data.streamId:'';
    }catch{
      streamIsLive=false;
      streamTitle='';
      streamId='';
    }finally{paint()}
  }

  document.addEventListener('asteriax:language-change',()=>{adoptLanguageToggle();paint()});
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)void refreshLive()});
  window.addEventListener('online',refreshLive);
  setInterval(()=>{if(!document.hidden)void refreshLive()},60000);
  adoptLanguageToggle();
  paint();
  void refreshLive();
})();

