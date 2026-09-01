(()=>{
  const norm=v=>String(v??'').toLowerCase().replace(/_/g,'-').replace(/\s+/g,'-');
  function statusOf(v){
    if(Number(v?.price_min)>0||v?.in_game===true||v?.in_game===1||String(v?.in_game)==='true')return'disponible';
    const s=norm(v?.production_status);
    if(['flight-ready','flightready','hangar-ready','hangarready'].includes(s))return'disponible';
    if(['active-production','activeproduction'].includes(s))return'production';
    if(['long-term-production','longtermproduction'].includes(s))return'production';
    if(['in-concept','inconcept','concept'].includes(s))return'concept';
    return'autre';
  }
  const baseRender=renderVehicles;
  renderVehicles=function(){
    const q=$('#vehicleSearch').value.trim().toLowerCase();
    const type=$('#vehicleType').value;
    const m=$('#vehicleManufacturer').value;
    const list=state.vehicles.filter(v=>{
      const matchesSearch=!q||[v.name,v.name_full,v.manufacturer,v.roles].some(x=>String(x||'').toLowerCase().includes(q));
      const matchesManufacturer=!m||v.manufacturer===m;
      let matchesType=true;
      if(type==='ground')matchesType=Number(v.is_ground_vehicle)===1;
      else if(type==='ship')matchesType=Number(v.is_ground_vehicle)!==1;
      else if(type==='concept')matchesType=statusOf(v)==='concept';
      else if(type==='disponible')matchesType=statusOf(v)==='disponible';
      else if(type==='production')matchesType=statusOf(v)==='production';
      return matchesSearch&&matchesManufacturer&&matchesType;
    });
    $('#vehicleCount').textContent=`${list.length} résultat${list.length>1?'s':''}`;
    $('#vehicleGrid').innerHTML=list.length?list.slice(0,600).map(vehicleCard).join(''):'<div class="empty">Aucun vaisseau ne correspond à ces filtres.</div>';
    bindCards($('#vehicleGrid'));
  };
})();
