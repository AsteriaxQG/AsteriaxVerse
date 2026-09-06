(()=>{
  const q=s=>document.querySelector(s);
  const norm=v=>String(v??'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
  const tone=value=>{const s=norm(value);if(s.includes('operationnel')||s.includes('en ligne'))return'good';if(s.includes('incident majeur')||s.includes('hors ligne')||s.includes('non disponible'))return'bad';if(s.includes('degrade')||s.includes('maintenance')||s.includes('incident partiel'))return'warn';return'neutral'};
  function decorate(el,value){if(!el)return;el.classList.add('status-indicator');el.classList.remove('indicator-good','indicator-warn','indicator-bad','indicator-neutral');el.classList.add(`indicator-${tone(value)}`)}
  function setText(id,value){const el=q(id);if(!el)return;el.textContent=value;decorate(el,value)}
  function setEnv(prefix,data,label){let status=data?.status||((prefix==='Ptu'||prefix==='Eptu'||prefix==='Hotfix')?'Hors ligne':'Non publié');if(prefix==='Live'&&norm(status)==='operationnel')status='En ligne';if(prefix==='Eptu'&&norm(status)==='non verifie')status='Non disponible';const version=data?.version?`Alpha ${data.version}`:'—';const build=data?.build||label;const statusEl=q(`#home${prefix}Status`),versionEl=q(`#home${prefix}Version`),buildEl=q(`#home${prefix}Build`);if(statusEl){statusEl.textContent=status;decorate(statusEl,status)}if(versionEl)versionEl.textContent=version;if(buildEl){buildEl.textContent=build;buildEl.title=build}}
  async function refresh(){
    try{
      const data=await window.AsteriaxApi.getJson('/api/status',{ttlMs:15000});if(!data.ok)throw 0;
      setEnv('Live',data.live,'Version LIVE officielle');setEnv('Hotfix',data.hotfix,'Aucun hotfix actif');setEnv('Ptu',data.ptu,'Public Test Universe');setEnv('Eptu',data.eptu,'Experimental PTU');
      setText('#homePuStatus',data.services?.persistentUniverse||'Inconnu');setText('#homePlatformStatus',data.services?.platform||'Inconnu');setText('#homeArenaStatus',data.services?.arenaCommander||'Inconnu');
      q('#homePlayers')?.closest('div')?.remove();
      let overallText=data.live?.status||data.services?.persistentUniverse||'Inconnu';if(norm(overallText)==='operationnel')overallText='En ligne';const overall=q('#verseOverallStatus');if(overall){overall.textContent=overallText;overall.className=`verse-overall ${tone(overallText)} status-indicator indicator-${tone(overallText)}`}
      if(q('#verseStatusSummary'))q('#verseStatusSummary').textContent=`Persistent Universe : ${data.services?.persistentUniverse||'Inconnu'} · LIVE ${data.live?.version?`Alpha ${data.live.version}`:'version inconnue'}`;
      if(q('#verseSourceNote')){const d=new Date(data.updatedAt);q('#verseSourceNote').textContent=`Sources officielles RSI · actualisé ${d.toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'})}`}
    }catch(e){const overall=q('#verseOverallStatus');if(overall){overall.textContent='Statut indisponible';overall.className='verse-overall warn status-indicator indicator-warn'}}
  }
  const ids=['#verseOverallStatus','#homeLiveStatus','#homeHotfixStatus','#homePtuStatus','#homeEptuStatus','#homePuStatus','#homePlatformStatus','#homeArenaStatus'];
  function watch(){for(const id of ids){const el=q(id);if(!el)continue;decorate(el,el.textContent);new MutationObserver(()=>decorate(el,el.textContent)).observe(el,{childList:true,characterData:true,subtree:true})}}
  q('#homePlayers')?.closest('div')?.remove();watch();refresh();setInterval(refresh,120000);
})();

