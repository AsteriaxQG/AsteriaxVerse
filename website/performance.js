function paginateList(list,page,pageSize){const totalPages=Math.max(1,Math.ceil(list.length/pageSize));const current=Math.min(Math.max(1,Math.trunc(Number(page)||1)),totalPages);const start=(current-1)*pageSize;return{items:list.slice(start,start+pageSize),current,totalPages,total:list.length}}
(()=>{
  const grid=document.querySelector('#itemGrid');
  const count=document.querySelector('#itemCount');
  const sort=document.querySelector('#itemSort');
  if(!grid||!count||!sort)return;

  const pagerStyle=document.createElement('style');
  pagerStyle.id='catalogPaginationStyles';
  pagerStyle.textContent='.catalog-pagination{display:flex;align-items:center;justify-content:center;gap:.45rem;flex-wrap:wrap;margin:1rem 0 1.5rem;padding:.5rem}.catalog-pagination button{min-height:40px;padding:.55rem .8rem;border:1px solid #21485b;border-radius:10px;background:linear-gradient(145deg,rgba(18,42,56,.94),rgba(8,22,31,.96));color:#d8f4ff;font:inherit;cursor:pointer;transition:border-color .16s,background .16s,transform .16s}.catalog-pagination button:hover:not(:disabled){border-color:#39c9f2;background:linear-gradient(145deg,rgba(20,69,91,.96),rgba(8,34,48,.98));transform:translateY(-1px)}.catalog-pagination button:disabled{opacity:.42;cursor:not-allowed}.catalog-pagination button[aria-current=page]{border-color:#35d8ff;background:linear-gradient(135deg,#087ab8,#07527f);color:white;box-shadow:0 0 18px rgba(39,198,242,.2)}.catalog-pagination span{padding:.45rem;color:#9bb2bf}@media(max-width:520px){.catalog-pagination{gap:.3rem;padding:.4rem .15rem}.catalog-pagination button{min-height:42px;padding:.55rem .62rem;font-size:.9rem}}';
  if(!document.querySelector('#catalogPaginationStyles')){document.head.append(pagerStyle)}

  const ITEM_PAGE_SIZE=48;
  let currentPage=1,lastFilterKey='';
  const pager=document.createElement('nav');
  pager.id='itemPagination';
  pager.className='catalog-pagination';
  pager.setAttribute('aria-label','Pages du catalogue des équipements');
  grid.insertAdjacentElement('afterend',pager);

  const text=v=>String(v??'');
  const numeric=v=>{const n=Number(v);return Number.isFinite(n)&&n>0?n:null};
  function sorted(list){
    const mode=sort.value||'name';
    return [...list].sort((a,b)=>{
      if(mode==='price'||mode==='price-desc'){
        const av=numeric(a.price_min),bv=numeric(b.price_min);
        if((av===null)!==(bv===null))return av===null?1:-1;
        if(av!==null&&bv!==null)return mode==='price'?av-bv:bv-av;
      }
      return text(a.name).localeCompare(text(b.name),'fr',{numeric:true});
    });
  }
  function pages(total,current){
    if(total<=7)return Array.from({length:total},(_,i)=>i+1);
    const values=[1];
    if(current>3)values.push('start-gap');
    for(let n=Math.max(2,current-1);n<=Math.min(total-1,current+1);n++)values.push(n);
    if(current<total-2)values.push('end-gap');
    values.push(total);
    return values;
  }
  function renderPager(totalPages){
    if(totalPages<=1){pager.replaceChildren();pager.hidden=true;return}
    pager.hidden=false;
    const numbered=pages(totalPages,currentPage).map(value=>typeof value==='number'?`<button type="button" data-item-page="${value}" ${value===currentPage?'class="active" aria-current="page"':''} aria-label="Page ${value}">${value}</button>`:'<span aria-hidden="true">…</span>').join('');
    pager.innerHTML=`<button type="button" data-item-page="${currentPage-1}" ${currentPage===1?'disabled':''} aria-label="Page précédente">← Précédent</button>${numbered}<button type="button" data-item-page="${currentPage+1}" ${currentPage===totalPages?'disabled':''} aria-label="Page suivante">Suivant →</button>`;
  }
  renderItems=function(){
    const q=document.querySelector('#itemSearch')?.value.trim().toLowerCase()||'';
    const section=document.querySelector('#itemSection')?.value||'';
    const size=document.querySelector('#itemSize')?.value||'';
    const filterKey=[q,section,size,sort.value].join('|');
    if(filterKey!==lastFilterKey){currentPage=1;lastFilterKey=filterKey}
    const list=sorted(state.items.filter(item=>(!q||[item.name,item.manufacturer,item.category].some(value=>text(value).toLowerCase().includes(q)))&&(!section||item.section===section)&&(!size||text(item.size)===size)));
    const totalPages=Math.max(1,Math.ceil(list.length/ITEM_PAGE_SIZE));
    currentPage=Math.min(currentPage,totalPages);
    const start=(currentPage-1)*ITEM_PAGE_SIZE;
    count.textContent=list.length?`${list.length} résultat${list.length>1?'s':''} · page ${currentPage} sur ${totalPages}`:'0 résultat';
    grid.innerHTML=list.length?list.slice(start,start+ITEM_PAGE_SIZE).map(itemCard).join(''):'<div class="empty">Aucun équipement ne correspond à ces filtres.</div>';
    bindCards(grid);
    renderPager(list.length?totalPages:0);
  };
  pager.addEventListener('click',event=>{
    const button=event.target.closest('[data-item-page]');
    if(!button||button.disabled)return;
    const next=Number(button.dataset.itemPage);
    if(!Number.isInteger(next)||next<1||next===currentPage)return;
    currentPage=next;renderItems();
    document.querySelector('#equipment')?.scrollIntoView({behavior:'smooth',block:'start'});
  });
  sort.addEventListener('change',()=>renderItems());

  const vehicleGrid=document.querySelector('#vehicleGrid'),vehicleCount=document.querySelector('#vehicleCount');
  if(vehicleGrid&&vehicleCount){
    const vehiclePager=document.querySelector('#vehiclePagination')||document.createElement('nav');
    vehiclePager.id='vehiclePagination';
    vehiclePager.className='catalog-pagination';
    vehiclePager.setAttribute('aria-label','Pages du catalogue des vaisseaux');
    const isMobile=()=>window.matchMedia('(max-width: 720px)').matches;
    let vehiclePage=1,lastVehicleFilterKey='';
    function renderVehiclePager(totalPages,english){
      if(totalPages<=1){vehiclePager.replaceChildren();vehiclePager.hidden=true;return}
      vehiclePager.hidden=false;
      const numbered=pages(totalPages,vehiclePage).map(value=>typeof value==='number'?'<button type="button" data-ship-page="'+value+'" '+(value===vehiclePage?'class="active" aria-current="page"':'')+' aria-label="Page '+value+'">'+value+'</button>':'<span aria-hidden="true">…</span>').join('');
      vehiclePager.innerHTML='<button type="button" data-ship-page="'+(vehiclePage-1)+'" '+(vehiclePage===1?'disabled':'')+' aria-label="'+(english?'Previous page':'Page précédente')+'">'+(english?'← Previous':'← Précédent')+'</button>'+numbered+'<button type="button" data-ship-page="'+(vehiclePage+1)+'" '+(vehiclePage===totalPages?'disabled':'')+' aria-label="'+(english?'Next page':'Suivant →')+'">'+(english?'Next →':'Suivant →')+'</button>';
    }
    if(!vehiclePager.isConnected)vehicleGrid.insertAdjacentElement('afterend',vehiclePager);
    renderVehicles=function(){
      const search=document.querySelector('#vehicleSearch')?.value.trim().toLowerCase()||'';
      const type=document.querySelector('#vehicleType')?.value||'';
      const manufacturer=document.querySelector('#vehicleManufacturer')?.value||'';
      const sortMode=document.querySelector('#vehicleSort')?.value||'name';
      const statusApi=window.AsteriaxVehicleFilters;
      const activeStatus=statusApi?.getStatusFilter?.()||'all';
      const pageSize=isMobile()?24:48;
      const filterKey=[search,type,manufacturer,sortMode,activeStatus,pageSize].join('|');
      if(filterKey!==lastVehicleFilterKey){vehiclePage=1;lastVehicleFilterKey=filterKey}
      const scope=state.vehicles.filter(v=>(!search||[v.name,v.name_full,v.manufacturer,v.roles].some(value=>String(value||'').toLowerCase().includes(search)))&&(!manufacturer||v.manufacturer===manufacturer)&&(!type||(type==='ground'?Number(v.is_ground_vehicle)===1:Number(v.is_ground_vehicle)!==1)));
      statusApi?.updateCounts(scope);
      const list=statusApi?.displayList?.(scope)||scope;
      const page=paginateList(list,vehiclePage,pageSize);
      vehiclePage=page.current;
      const english=window.AsteriaxI18n?.isEnglish?.()===true;
      vehicleCount.textContent=list.length?(english?list.length+' results · page '+vehiclePage+' of '+page.totalPages:list.length+' résultat'+(list.length>1?'s':'')+' · page '+vehiclePage+' sur '+page.totalPages):(english?'0 results':'0 résultat');
      vehicleGrid.innerHTML=page.total?page.items.map((vehicle,index)=>vehicleCard(vehicle,index)).join(''):'<div class="empty">'+(english?'No ships match these filters.':'Aucun vaisseau ne correspond à ces filtres.')+'</div>';
      bindCards(vehicleGrid);
      renderVehiclePager(list.length?page.totalPages:0,english);
    };
    vehiclePager.addEventListener('click',event=>{
      const button=event.target.closest('[data-ship-page]');
      if(!button||button.disabled)return;
      const next=Number(button.dataset.shipPage);
      if(!Number.isInteger(next)||next<1||next===vehiclePage)return;
      vehiclePage=next;renderVehicles();
      document.querySelector('#vehicles')?.scrollIntoView({behavior:'smooth',block:'start'});
    });
    const breakpoint=window.matchMedia('(max-width: 720px)');
    const onBreakpointChange=()=>{vehiclePage=1;lastVehicleFilterKey='';renderVehicles()};
    if(breakpoint.addEventListener)breakpoint.addEventListener('change',onBreakpointChange);
    else breakpoint.addListener?.(onBreakpointChange);
  }

})();
