(()=>{
  const grid=document.querySelector('#homeNowGrid');
  if(!grid)return;

  function ageMinutes(value=''){
    const text=String(value).trim().toLowerCase();
    let m=text.match(/^il y a\s+(\d+)\s+(minute|minutes|heure|heures|jour|jours|semaine|semaines|mois|an|ans)$/i);
    if(m){
      const n=Number(m[1]);
      const factors={minute:1,minutes:1,heure:60,heures:60,jour:1440,jours:1440,semaine:10080,semaines:10080,mois:43800,an:525600,ans:525600};
      return n*(factors[m[2]]||Number.MAX_SAFE_INTEGER);
    }
    m=text.match(/^(\d+|a|an|one)\s+(minute|hour|day|week|month|year)s?\s+ago$/i);
    if(m){
      const n=/^(a|an|one)$/i.test(m[1])?1:Number(m[1]);
      const factors={minute:1,hour:60,day:1440,week:10080,month:43800,year:525600};
      return n*(factors[m[2]]||Number.MAX_SAFE_INTEGER);
    }
    return Number.MAX_SAFE_INTEGER;
  }

  let sorting=false;
  function sortNewestFirst(){
    if(sorting)return;
    const cards=[...grid.querySelectorAll(':scope > .home-now-card')];
    if(cards.length<2)return;
    const sorted=[...cards].sort((a,b)=>ageMinutes(a.querySelector('small')?.textContent)-ageMinutes(b.querySelector('small')?.textContent));
    if(sorted.every((card,i)=>card===cards[i]))return;
    sorting=true;
    sorted.forEach(card=>grid.appendChild(card));
    queueMicrotask(()=>{sorting=false});
  }

  new MutationObserver(sortNewestFirst).observe(grid,{childList:true,subtree:true,characterData:true});
  sortNewestFirst();
})();