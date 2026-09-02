(()=>{
  const VERIFIED_STATUS=new Map([
    ['odyssey','concept'],['misc odyssey','concept'],
    ['vulcan','concept'],['aegis vulcan','concept'],
    ['pioneer','concept'],['consolidated outland pioneer','concept']
  ]);
  const NON_HULL=new Set(['valkyrie liberator edition','valkyrie 2948 liberator edition','anvil valkyrie liberator edition','anvil valkyrie 2948 liberator edition']);
  const norm=v=>String(v||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
  function apply(){
    let vehicles;
    try{vehicles=state?.vehicles}catch{}
    if(!Array.isArray(vehicles)||!vehicles.length)return false;
    let changed=false;
    for(let i=vehicles.length-1;i>=0;i--){
      const v=vehicles[i],n=norm(v.name_full||v.name);
      if(NON_HULL.has(n)){vehicles.splice(i,1);changed=true;continue;}
      const status=VERIFIED_STATUS.get(n);
      if(status&&v.production_status!==status){v.production_status=status;changed=true;}
    }
    if(changed){try{renderActiveCatalog()}catch{}}
    return true;
  }
  let attempts=0;
  function wait(){attempts++;if(!apply()&&attempts<80)setTimeout(wait,150)}
  wait();
  document.addEventListener('asteriax:catalog-ready',apply);
})();
