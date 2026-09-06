(()=>{
  const pageList=document.querySelector('#releaseList'),key='ax_changelog_seen';let versions=[],seen='',failed=false,observer,overlay=null,lastFocus=null;
  try{seen=localStorage.getItem(key)||''}catch{}
  const en=()=>window.AsteriaxI18n?.isEnglish?.()===true;
  const text=(tag,value,cls)=>{const el=document.createElement(tag);el.textContent=value;if(cls)el.className=cls;return el};
  const listTarget=()=>pageList||overlay?.querySelector('[data-release-list]');
  function markSeen(){if(!versions.length)return;seen=versions[0].version;try{localStorage.setItem(key,seen)}catch{}paintBadges()}
  function paintBadges(){const english=en();document.querySelectorAll('[data-changelog-label]').forEach(el=>el.textContent=english?'Website updates':'Nouveautés du site');document.querySelectorAll('[data-changelog-badge]').forEach(el=>{el.textContent=english?'NEW':'NOUVEAU';el.hidden=!versions.length||seen===versions[0].version})}
  function renderList(list){
    if(!list)return;const english=en(),lang=english?'en':'fr';observer?.disconnect();list.replaceChildren();
    if(!versions.length){list.append(text('p',failed?(english?'Updates unavailable. Please reload to retry.':'Nouveautés indisponibles. Recharge la page pour réessayer.'):(english?'Loading…':'Chargement…'),'ax-release-empty'));return}
    for(const [i,v] of versions.entries()){
      const card=text('article','','ax-release-card'),head=text('div','','ax-release-meta');
      head.append(text('strong','v'+v.version));const date=text('time',new Date(v.date+'T12:00:00Z').toLocaleDateString(english?'en-GB':'fr-FR',{dateStyle:'long',timeZone:'UTC'}));date.dateTime=v.date;head.append(date);
      if(!i&&seen!==v.version)head.append(text('span',english?'NEW':'NOUVEAU','ax-release-new'));
      card.append(head,text('h2',v.title[lang]));
      for(const [category,fr,eng] of [['new','✨ Nouveautés','✨ New'],['ui','🎨 Interface','🎨 Interface'],['fixes','🐛 Corrections','🐛 Fixes'],['technical','⚙️ Technique','⚙️ Technical']]){
        if(!Array.isArray(v[category])||!v[category].length)continue;
        card.append(text('h3',english?eng:fr));const ul=document.createElement('ul');v[category].forEach(item=>ul.append(text('li',item[lang])));card.append(ul);
      }
      list.append(card);
    }
    observer=new IntersectionObserver(entries=>{if(document.hidden||!entries.some(e=>e.isIntersecting))return;markSeen();observer.disconnect()},{threshold:0.1});
    observer.observe(list.firstElementChild);
  }
  function paint(){
    const english=en();paintBadges();
    if(pageList){document.title=english?'Asteriax Verse — Updates':'Asteriax Verse — Nouveautés';const title=document.querySelector('#releaseTitle'),intro=document.querySelector('#releaseIntro');if(title)title.textContent=english?'Changelog / Updates':'Changelog / Nouveautés';if(intro)intro.textContent=english?'Website improvements, release by release.':'Les évolutions du site, version après version.'}
    if(overlay){overlay.querySelector('[data-overlay-title]').textContent=english?'Website updates':'Nouveautés du site';overlay.querySelector('[data-overlay-intro]').textContent=english?'Latest Asteriax Verse changes without leaving your page.':'Les dernières évolutions d’Asteriax Verse sans quitter ta page.';overlay.querySelector('[data-overlay-back]').textContent=english?'← Back':'← Retour';overlay.querySelector('[data-overlay-close]').setAttribute('aria-label',english?'Close updates':'Fermer les nouveautés')}
    renderList(listTarget());
  }
  function buildOverlay(){
    if(pageList||overlay)return;
    overlay=document.createElement('div');overlay.className='ax-changelog-overlay';overlay.hidden=true;overlay.setAttribute('aria-hidden','true');
    overlay.innerHTML='<div class="ax-changelog-backdrop" data-overlay-dismiss></div><section class="ax-changelog-panel" role="dialog" aria-modal="true" aria-labelledby="axChangelogOverlayTitle"><header class="ax-changelog-panel-head"><button type="button" class="ax-changelog-back" data-overlay-back>← Retour</button><div><p class="eyebrow">ASTERIAX VERSE</p><h2 id="axChangelogOverlayTitle" data-overlay-title>Nouveautés du site</h2><p data-overlay-intro>Les dernières évolutions d’Asteriax Verse sans quitter ta page.</p></div><button type="button" class="ax-changelog-close" data-overlay-close aria-label="Fermer les nouveautés">×</button></header><div class="ax-changelog-scroll"><div class="ax-release-list" data-release-list aria-live="polite"><p>Chargement…</p></div><a class="ax-changelog-full-link" href="/changelog.html">Ouvrir la page complète ↗</a></div></section>';
    document.body.append(overlay);
    overlay.querySelectorAll('[data-overlay-dismiss],[data-overlay-close],[data-overlay-back]').forEach(el=>el.addEventListener('click',closeOverlay));
  }
  function openOverlay(event){
    if(pageList)return;if(event){event.preventDefault()}buildOverlay();lastFocus=document.activeElement;overlay.hidden=false;overlay.setAttribute('aria-hidden','false');document.body.classList.add('ax-changelog-open');paint();requestAnimationFrame(()=>overlay.classList.add('is-open'));setTimeout(()=>overlay.querySelector('[data-overlay-close]')?.focus(),30);
  }
  function closeOverlay(){
    if(!overlay||overlay.hidden)return;overlay.classList.remove('is-open');document.body.classList.remove('ax-changelog-open');setTimeout(()=>{overlay.hidden=true;overlay.setAttribute('aria-hidden','true');lastFocus?.focus?.()},180)
  }
  function bindTriggers(){if(pageList)return;document.querySelectorAll('a.ax-changelog-link[href*="changelog"]').forEach(link=>{if(link.dataset.overlayBound)return;link.dataset.overlayBound='1';link.addEventListener('click',openOverlay)})}
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&overlay&&!overlay.hidden)closeOverlay()});
  document.addEventListener('asteriax:language-change',paint);
  window.addEventListener('storage',event=>{if(event.key===key){seen=event.newValue||'';paint()}});
  bindTriggers();paint();
  fetch('/api/changelog',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error();return r.json()}).then(data=>{versions=data.versions;if(!Array.isArray(versions)||!versions.length)throw Error();paint()}).catch(()=>{versions=[];failed=true;paint()});
})();
