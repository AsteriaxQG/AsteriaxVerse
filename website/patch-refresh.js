(()=>{
  const button=document.querySelector('.home-live-row .home-live-icon');
  const title=document.querySelector('#homePatchTitle');
  const posted=document.querySelector('#homePatchPosted');
  if(!button||!title||!posted)return;

  const copy=title.closest('.home-live-copy');
  const feedback=document.createElement('span');
  feedback.className='patch-refresh-feedback';
  feedback.setAttribute('role','status');
  feedback.setAttribute('aria-live','polite');
  if(copy)copy.appendChild(feedback);
  let feedbackTimer=null;

  const postedLabel=value=>{
    const text=String(value||'').trim();
    const m=text.match(/^(\d+|an?|one)\s+(minute|hour|day|week|month|year)s?\s+ago$/i);
    if(!m)return text;
    const amount=/^(?:a|an|one)$/i.test(m[1])?1:Number(m[1]);
    const units={minute:['minute','minutes'],hour:['heure','heures'],day:['jour','jours'],week:['semaine','semaines'],month:['mois','mois'],year:['an','ans']};
    const unit=units[m[2].toLowerCase()];
    return `il y a ${amount} ${unit[amount===1?0:1]}`;
  };

  function showFeedback(text,tone='',duration=2800){
    if(!feedback)return;
    clearTimeout(feedbackTimer);
    feedback.textContent=text;
    feedback.className=`patch-refresh-feedback${tone?` ${tone}`:''} visible`;
    if(duration>0){
      feedbackTimer=setTimeout(()=>{
        feedback.classList.remove('visible');
        setTimeout(()=>{if(!feedback.classList.contains('visible'))feedback.textContent=''},180);
      },duration);
    }
  }

  async function refreshPatch(force=false,manual=false){
    if(button.dataset.loading==='1')return;
    const previousTitle=title.textContent.trim();
    const previousPosted=posted.textContent.trim();
    button.dataset.loading='1';
    button.classList.add('is-refreshing');
    button.setAttribute('aria-busy','true');
    button.title='Actualisation du dernier patch…';
    if(manual)showFeedback('Vérification…','checking',0);
    try{
      const url=`/api/news?${force?'refresh=1&':''}patch_refresh=${Date.now()}`;
      const data=await window.AsteriaxApi.getJson(url,{force,ttlMs:120000});
      const items=Array.isArray(data.items)?data.items:[];
      const patch=items.find(x=>x.category==='PATCH')||items[0];
      if(!patch)throw new Error('Aucun patch trouvé');
      const nextTitle=patch.title||'Dernier patch Star Citizen';
      const nextPosted=postedLabel(patch.posted||'');
      const changed=nextTitle!==previousTitle||nextPosted!==previousPosted;
      title.textContent=nextTitle;
      posted.textContent=nextPosted;
      button.title='Actualisé maintenant · cliquer pour forcer une nouvelle vérification';
      if(manual)showFeedback(changed?'Mis à jour':'Déjà à jour',changed?'updated':'current');
    }catch(e){
      button.title='Impossible d’actualiser pour le moment · cliquer pour réessayer';
      if(manual)showFeedback('Impossible de vérifier','error');
    }finally{
      button.dataset.loading='0';
      button.classList.remove('is-refreshing');
      button.setAttribute('aria-busy','false');
    }
  }

  button.setAttribute('role','button');
  button.setAttribute('tabindex','0');
  button.setAttribute('aria-label','Actualiser le dernier patch Star Citizen');
  button.title='Actualiser le dernier patch';
  button.addEventListener('click',()=>refreshPatch(true,true));
  button.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();refreshPatch(true,true)}});

  // Vérification automatique toutes les 5 minutes, sans message intrusif.
  setInterval(()=>refreshPatch(false,false),5*60*1000);
  // Et une vérification silencieuse quand l’utilisateur revient sur l’onglet.
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)refreshPatch(false,false)});
})();
