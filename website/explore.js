(()=>{
  const home=document.querySelector('#exploreHome');
  const panel=document.querySelector('#exploreDirectory');
  const search=document.querySelector('#exploreSearch');
  const mg=document.querySelector('#manufacturerGrid');
  const lg=document.querySelector('#locationGrid');
  const label=document.querySelector('#exploreLabel');
  const title=document.querySelector('#exploreTitle');
  const backBtn=document.querySelector('#exploreBack');
  if(!home||!panel||!search||!mg||!lg||!backBtn)return;

  let mode='';
  const norm=v=>String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();

  function show(el,yes){el.classList.toggle('is-hidden',!yes);el.hidden=!yes;}
  function filter(){
    const grid=mode==='manufacturers'?mg:lg;
    if(!grid)return;
    const q=norm(search.value);
    grid.querySelectorAll('.directory-card').forEach(card=>card.classList.toggle('filtered-out',!!q&&!norm(card.textContent).includes(q)));
  }
  function openDirectory(next){
    mode=next;
    show(home,false);show(panel,true);
    show(mg,next==='manufacturers');show(lg,next==='locations');
    label.textContent=next==='manufacturers'?'MARQUES & FABRICANTS':'BOUTIQUES & DESTINATIONS';
    title.textContent=next==='manufacturers'?'Constructeurs':'Lieux d’achat';
    search.placeholder=next==='manufacturers'?'Rechercher un constructeur…':'Rechercher une ville, station ou boutique…';
    search.value='';filter();
    panel.scrollIntoView({behavior:'smooth',block:'start'});
  }
  function reset(){
    mode='';search.value='';
    show(panel,false);show(mg,false);show(lg,false);show(home,true);
    mg.querySelectorAll('.directory-card').forEach(c=>c.classList.remove('filtered-out'));
    lg.querySelectorAll('.directory-card').forEach(c=>c.classList.remove('filtered-out'));
  }

  home.querySelectorAll('[data-explore-mode]').forEach(btn=>btn.addEventListener('click',()=>openDirectory(btn.dataset.exploreMode)));
  backBtn.addEventListener('click',reset);
  search.addEventListener('input',filter);
  document.querySelectorAll('.nav-btn[data-view="explore"]').forEach(btn=>btn.addEventListener('click',reset));
  reset();
})();
