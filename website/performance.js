(()=>{
  const grid=document.querySelector('#itemGrid');
  const count=document.querySelector('#itemCount');
  const sort=document.querySelector('#itemSort');
  if(!grid||!count||!sort)return;

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
})();
