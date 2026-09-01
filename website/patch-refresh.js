(()=>{
  const button=document.querySelector('.home-live-row .home-live-icon');
  const title=document.querySelector('#homePatchTitle');
  const posted=document.querySelector('#homePatchPosted');
  if(!button||!title||!posted)return;

  const postedLabel=value=>{
    const text=String(value||'').trim();
    const m=text.match(/^(\d+|an?|one)\s+(minute|hour|day|week|month|year)s?\s+ago$/i);
    if(!m)return text;
    const amount=/^(?:a|an|one)$/i.test(m[1])?1:Number(m[1]);
    const units={minute:['minute','minutes'],hour:['heure','heures'],day:['jour','jours'],week:['semaine','semaines'],month:['mois','mois'],year:['an','ans']};
    const unit=units[m[2].toLowerCase()];
    return `il y a ${amount} ${unit[amount===1?0:1]}`;
  };

  async function refreshPatch(force=false){
    if(button.dataset.loading==='1')return;
    button.dataset.loading='1';
    button.classList.add('is-refreshing');
    button.setAttribute('aria-busy','true');
    button.title='Actualisation du dernier patch…';
    try{
      const url=`/api/news?${force?'refresh=1&':''}patch_refresh=${Date.now()}`;
      const res=await fetch(url,{headers:{Accept:'application/json'},cache:'no-store'});
      if(!res.ok)throw new Error('Flux RSI indisponible');
      const data=await res.json();
      const items=Array.isArray(data.items)?data.items:[];
      const patch=items.find(x=>x.category==='PATCH')||items[0];
      if(!patch)throw new Error('Aucun patch trouvé');
      title.textContent=patch.title||'Dernier patch Star Citizen';
      posted.textContent=postedLabel(patch.posted||'');
      button.title=`Actualisé maintenant · cliquer pour forcer une nouvelle vérification`;
    }catch(e){
      button.title='Impossible d’actualiser pour le moment · cliquer pour réessayer';
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
  button.addEventListener('click',()=>refreshPatch(true));
  button.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();refreshPatch(true)}});

  // Vérification automatique toutes les 5 minutes.
  setInterval(()=>refreshPatch(false),5*60*1000);
  // Et une vérification quand l’utilisateur revient sur l’onglet après un moment.
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)refreshPatch(false)});
})();
