(()=>{
  const typeEl=document.querySelector('#vehicleType');
  const filters=document.querySelector('#vehicles .filters');
  if(!typeEl||!filters)return;
  let statusFilter='all';
  typeEl.innerHTML='<option value="">Tous les types</option><option value="ship">Vaisseaux</option><option value="ground">Véhicules terrestres</option>';

  const bar=document.createElement('div');
  bar.className='ship-status-filter';
  bar.innerHTML='<span class="ship-status-label">Statut</span><button class="active" data-ship-status="all">Tous <b data-count="all"></b></button><button data-ship-status="disponible">Disponible <b data-count="disponible"></b></button><button data-ship-status="production">En production <b data-count="production"></b></button><button data-ship-status="concept">En concept <b data-count="concept"></b></button>';
  filters.appendChild(bar);

  const style=document.createElement('style');
  style.textContent='.ship-status-filter{grid-column:1/-1;display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:4px 2px 0}.ship-status-label{margin-right:4px;color:#6d8c9b;font-size:10px;font-weight:900;letter-spacing:1.4px;text-transform:uppercase}.ship-status-filter button{appearance:none;border:1px solid #234454;border-radius:999px;background:#0b1922;color:#91aab6;padding:8px 12px;font:inherit;font-size:11px;font-weight:800;cursor:pointer;transition:.16s}.ship-status-filter button:hover{border-color:#39768d;color:#e4f9ff;background:#10232e}.ship-status-filter button.active{border-color:#49a6c5;background:#123242;color:#eafcff;box-shadow:inset 0 0 0 1px rgba(82,217,255,.08)}.ship-status-filter b{display:inline-block;margin-left:5px;color:#638795;font-size:9px}.ship-status-filter button.active b{color:#83dff9}@media(max-width:650px){.ship-status-filter{flex-wrap:nowrap;overflow-x:auto;padding-bottom:3px}.ship-status-label{display:none}.ship-status-filter button{flex:0 0 auto}}';
  document.head.appendChild(style);

  const norm=v=>String(v??'').toLowerCase().replace(/_/g,'-').replace(/\s+/g,'-');
  function statusOf(v){
    if(Number(v?.price_min)>0||v?.in_game===true||v?.in_game===1||String(v?.in_game)==='true')return'disponible';
    const s=norm(v?.production_status);
    if(['flight-ready','flightready','hangar-ready','hangarready'].includes(s))return'disponible';
    if(['active-production','activeproduction','long-term-production','longtermproduction'].includes(s))return'production';
    if(['in-concept','inconcept','concept'].includes(s))return'concept';
    return'autre';
  }
  const num=v=>Number(v)||0;
  function sortList(list){
    const sort=document.querySelector('#vehicleSort')?.value||'name';
    return [...list].sort((a,b)=>{
      if(sort==='price')return (num(a.price_min)||Number.MAX_SAFE_INTEGER)-(num(b.price_min)||Number.MAX_SAFE_INTEGER);
      if(sort==='price-desc')return num(b.price_min)-num(a.price_min);
      if(sort==='scu')return num(b.scu)-num(a.scu);
      return String(a.name||'').localeCompare(String(b.name||''),'fr',{numeric:true});
    });
  }
  function scopeList(){
    const q=document.querySelector('#vehicleSearch')?.value.trim().toLowerCase()||'';
    const type=typeEl.value;
    const m=document.querySelector('#vehicleManufacturer')?.value||'';
    return state.vehicles.filter(v=>{
      const matchesSearch=!q||[v.name,v.name_full,v.manufacturer,v.roles].some(x=>String(x||'').toLowerCase().includes(q));
      const matchesManufacturer=!m||v.manufacturer===m;
      const matchesType=!type||(type==='ground'?Number(v.is_ground_vehicle)===1:Number(v.is_ground_vehicle)!==1);
      return matchesSearch&&matchesManufacturer&&matchesType;
    });
  }
  function updateCounts(scope){
    const counts={all:scope.length,disponible:0,production:0,concept:0};
    scope.forEach(v=>{const s=statusOf(v);if(counts[s]!==undefined)counts[s]++});
    Object.entries(counts).forEach(([k,n])=>{const el=bar.querySelector(`[data-count="${k}"]`);if(el)el.textContent=n});
  }
  renderVehicles=function(){
    const scope=scopeList();
    updateCounts(scope);
    const list=sortList(statusFilter==='all'?scope:scope.filter(v=>statusOf(v)===statusFilter));
    document.querySelector('#vehicleCount').textContent=`${list.length} résultat${list.length>1?'s':''}`;
    const grid=document.querySelector('#vehicleGrid');
    grid.innerHTML=list.length?list.slice(0,600).map(vehicleCard).join(''):'<div class="empty">Aucun vaisseau ne correspond à ces filtres.</div>';
    bindCards(grid);
  };
  bar.querySelectorAll('[data-ship-status]').forEach(btn=>btn.addEventListener('click',()=>{
    statusFilter=btn.dataset.shipStatus;
    bar.querySelectorAll('[data-ship-status]').forEach(x=>x.classList.toggle('active',x===btn));
    renderVehicles();
  }));
  document.querySelector('#vehicleSort')?.addEventListener('change',renderVehicles);
})();
