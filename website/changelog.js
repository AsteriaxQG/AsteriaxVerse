(()=>{
  const list=document.querySelector('#releaseList'),key='ax_changelog_seen';let versions=[],seen='',failed=false,observer;
  try{seen=localStorage.getItem(key)||''}catch{}
  const en=()=>window.AsteriaxI18n?.isEnglish?.()===true;
  const text=(tag,value,cls)=>{const el=document.createElement(tag);el.textContent=value;if(cls)el.className=cls;return el};
  function paint(){
    const english=en(),lang=english?'en':'fr';
    document.querySelectorAll('[data-changelog-label]').forEach(el=>el.textContent=english?'Website updates':'Nouveautés du site');
    document.querySelectorAll('[data-changelog-badge]').forEach(el=>{el.textContent=english?'NEW':'NOUVEAU';el.hidden=!versions.length||seen===versions[0].version});
    if(!list)return;
    document.title=english?'Asteriax Verse — Updates':'Asteriax Verse — Nouveautés';
    document.querySelector('#releaseTitle').textContent=english?'Changelog / Updates':'Changelog / Nouveautés';
    document.querySelector('#releaseIntro').textContent=english?'Website improvements, release by release.':'Les évolutions du site, version après version.';
    observer?.disconnect();list.replaceChildren();
    if(!versions.length){list.append(text('p',failed?(english?'Updates unavailable. Please reload to retry.':'Nouveautés indisponibles. Recharge la page pour réessayer.'):(english?'Loading…':'Chargement…')));return}
    for(const [i,v] of versions.entries()){
      const card=text('article','','ax-release-card'),head=text('div','','ax-release-meta');
      head.append(text('strong','v'+v.version));const date=text('time',new Date(v.date+'T12:00:00Z').toLocaleDateString(english?'en-GB':'fr-FR',{dateStyle:'long',timeZone:'UTC'}));date.dateTime=v.date;head.append(date);
      if(!i&&seen!==v.version)head.append(text('span',english?'NEW':'NOUVEAU','ax-release-new'));
      card.append(head,text('h2',v.title[lang]));
      for(const [category,fr,eng] of [['new','✨ Nouveautés','✨ New'],['ui','🎨 Interface','🎨 Interface'],['fixes','🐛 Corrections','🐛 Fixes'],['technical','⚙️ Technique','⚙️ Technical']]){
        if(!v[category].length)continue;
        card.append(text('h3',english?eng:fr));const ul=document.createElement('ul');v[category].forEach(item=>ul.append(text('li',item[lang])));card.append(ul);
      }
      list.append(card);
    }
    observer=new IntersectionObserver(entries=>{if(document.hidden||!entries.some(e=>e.isIntersecting))return;seen=versions[0].version;try{localStorage.setItem(key,seen)}catch{}observer.disconnect()},{threshold:0.1});
    observer.observe(list.firstElementChild);
  }
  document.addEventListener('asteriax:language-change',paint);
  window.addEventListener('storage',event=>{if(event.key===key){seen=event.newValue||'';paint()}});
  paint();fetch('/api/changelog',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error();return r.json()}).then(data=>{versions=data.versions;if(!Array.isArray(versions)||!versions.length)throw Error();paint()}).catch(()=>{versions=[];failed=true;paint()});
})();
