(()=>{
  const q=s=>document.querySelector(s);
  const norm=v=>String(v??'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
  const tone=value=>{const s=norm(value);if(s.includes('operationnel')||s.includes('en ligne'))return'good';if(s.includes('incident majeur')||s.includes('hors ligne'))return'bad';if(s.includes('degrade')||s.includes('maintenance')||s.includes('incident partiel'))return'warn';return'neutral'};
  const knownLiveBuild=version=>String(version||'').startsWith('4.10')?'4.10.0-live.12519617':'';
  function decorate(el,value){if(!el)return;el.classList.add('status-indicator');el.classList.remove('indicator-good','indicator-warn','indicator-bad','indicator-neutral');el.classList.add(`indicator-${tone(value)}`)}
  function setText(id,value){const el=q(id);if(!el)return;el.textContent=value;decorate(el,value)}
  function setEnv(prefix,data,label){const status=data?.status||((prefix==='Ptu'||prefix==='Eptu')?'Hors ligne':'Non publié');const version=data?.version?`Alpha ${data.version}`:'—';const fallback=prefix==='Live'?knownLiveBuild(data?.version):'';const build=data?.build||fallback||label;const statusEl=q(`#home${prefix}Status`),versionEl=q(`#home${prefix}Version`),buildEl=q(`#home${prefix}Build`);if(statusEl){statusEl.textContent=status;decorate(statusEl,status)}if(versionEl)versionEl.textContent=version;if(buildEl){buildEl.textContent=build;buildEl.title=build}}
  async function refresh(){
    try{
      const res=await fetch(`/api/status?ui=${Date.now()}`,{headers:{Accept:'application/json'},cache:'no-store'});if(!res.ok)throw 0;const data=await res.json();if(!data.ok)throw 0;
      setEnv('Live',data.live,'Version LIVE officielle');setEnv('Ptu',data.ptu,'Public Test Universe');setEnv('Eptu',data.eptu,'Experimental PTU');
      setText('#homePuStatus',data.services?.persistentUniverse||'Inconnu');setText('#homePlatformStatus',data.services?.platform||'Inconnu');setText('#homeArenaStatus',data.services?.arenaCommander||'Inconnu');
      q('#homePlayers')?.closest('div')?.remove();
      const overallText=data.live?.status||data.services?.persistentUniverse||'Inconnu';const overall=q('#verseOverallStatus');if(overall){overall.textContent=overallText;overall.className=`verse-overall ${tone(overallText)} status-indicator indicator-${tone(overallText)}`}
      if(q('#verseStatusSummary'))q('#verseStatusSummary').textContent=`Persistent Universe : ${data.services?.persistentUniverse||'Inconnu'} · LIVE ${data.live?.version?`Alpha ${data.live.version}`:'version inconnue'}`;
      if(q('#verseSourceNote')){const d=new Date(data.updatedAt);q('#verseSourceNote').textContent=`Sources officielles RSI · actualisé ${d.toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'})}`}
    }catch(e){const overall=q('#verseOverallStatus');if(overall){overall.textContent='Statut indisponible';overall.className='verse-overall warn status-indicator indicator-warn'}}
  }
  const ids=['#verseOverallStatus','#homeLiveStatus','#homePtuStatus','#homeEptuStatus','#homePuStatus','#homePlatformStatus','#homeArenaStatus'];
  function watch(){for(const id of ids){const el=q(id);if(!el)continue;decorate(el,el.textContent);new MutationObserver(()=>decorate(el,el.textContent)).observe(el,{childList:true,characterData:true,subtree:true})}}
  q('#homePlayers')?.closest('div')?.remove();watch();refresh();setInterval(refresh,120000);
})();
