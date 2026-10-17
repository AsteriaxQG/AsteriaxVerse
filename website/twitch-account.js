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
  let streamIsLive=false,streamTitle='';
  const english=()=>window.AsteriaxI18n?.isEnglish?.()===true;

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
  }

  async function refreshLive(){
    try{
      const response=await fetch('/api/twitch/live',{cache:'no-store',signal:AbortSignal.timeout(8000)});
      if(!response.ok)throw Error('Unavailable');
      const data=await response.json();
      const age=Date.now()-Date.parse(data.checkedAt);
      streamIsLive=data.live===true&&age>=0&&age<180000;
      streamTitle=typeof data.title==='string'?data.title:'';
    }catch{
      streamIsLive=false;
      streamTitle='';
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

