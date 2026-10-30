(()=>{
  const toggle=document.querySelector('.mobile-menu-toggle');
  const menu=document.querySelector('#mobileMenu');
  if(!toggle||!menu)return;
  const close=()=>{menu.hidden=true;toggle.setAttribute('aria-expanded','false');toggle.setAttribute('aria-label','Ouvrir le menu')};
  toggle.addEventListener('click',()=>{
    const open=menu.hidden;
    menu.hidden=!open;
    toggle.setAttribute('aria-expanded',String(open));
    toggle.setAttribute('aria-label',open?'Fermer le menu':'Ouvrir le menu');
  });
  menu.querySelectorAll('[data-mobile-go]').forEach(button=>button.addEventListener('click',()=>{
    document.querySelector(`.nav-btn[data-view="${button.dataset.mobileGo}"]`)?.click();
    close();
  }));
  document.addEventListener('click',event=>{if(!menu.hidden&&!menu.contains(event.target)&&!toggle.contains(event.target))close()});
  document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!menu.hidden){close();toggle.focus()}});
  document.addEventListener('asteriax:view-change',event=>{
    toggle.classList.toggle('active',['vehicles','equipment','iae','news'].includes(event.detail));
    close();
  });
  toggle.classList.toggle('active',['vehicles','equipment','iae','news'].includes(location.hash.slice(1)));
  window.matchMedia('(min-width: 901px)').addEventListener('change',close);
  const filterToggle=document.querySelector('.mobile-filters-toggle');
  const filters=document.querySelector('#vehicles .filters');
  const translateControls=()=>{
    const en=window.AsteriaxI18n?.isEnglish?.()===true;
    if(filterToggle)filterToggle.firstChild.textContent=en?'Filters and sort ':'Filtres et tri ';
    const news=menu.querySelector('[data-mobile-go="news"] span');
    if(news)news.textContent=en?'News':'Actus';
    const ships=menu.querySelector('[data-mobile-go="vehicles"] span');
    if(ships)ships.textContent=en?'Ships':'Vaisseaux';
    const equipment=menu.querySelector('[data-mobile-go="equipment"] span');
    if(equipment)equipment.textContent=en?'Equipment':'Équipements';
  };
  document.addEventListener('asteriax:language-change',translateControls);
  translateControls();
  filterToggle?.addEventListener('click',()=>{
    const open=filters.classList.toggle('is-open');
    filterToggle.setAttribute('aria-expanded',String(open));
  });
})();
