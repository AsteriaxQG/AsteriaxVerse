(()=>{
  const home=document.querySelector('#exploreHome'),panel=document.querySelector('#exploreDirectory'),search=document.querySelector('#exploreSearch');
  const mg=document.querySelector('#manufacturerGrid'),lg=document.querySelector('#locationGrid');
  if(!home||!panel||!mg||!lg)return;
  let mode='';
  const norm=v=>String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  function filter(){const q=norm(search.value);const grid=mode==='manufacturers'?mg:lg;grid.querySelectorAll('.directory-card').forEach(c=>c.hidden=!!q&&!norm(c.textContent).includes(q));}
  function open(next){mode=next;home.hidden=true;panel.hidden=false;mg.hidden=next!=='manufacturers';lg.hidden=next!=='locations';document.querySelector('#exploreLabel').textContent=next==='manufacturers'?'MARQUES & FABRICANTS':'BOUTIQUES & DESTINATIONS';document.querySelector('#exploreTitle').textContent=next==='manufacturers'?'Constructeurs':'Lieux d’achat';search.placeholder=next==='manufacturers'?'Rechercher un constructeur…':'Rechercher un lieu…';search.value='';filter();setTimeout(()=>search.focus(),50)}
  function back(){mode='';panel.hidden=true;home.hidden=false;search.value=''}
  home.querySelectorAll('[data-explore-mode]').forEach(b=>b.addEventListener('click',()=>open(b.dataset.exploreMode)));
  document.querySelector('#exploreBack').addEventListener('click',back);search.addEventListener('input',filter);
  document.querySelectorAll('.nav-btn[data-view="explore"]').forEach(b=>b.addEventListener('click',back));
})();
