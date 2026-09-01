(()=>{
  const VERIFIED_STATUS=new Map([
    ['odyssey','concept'],
    ['misc odyssey','concept']
  ]);
  const norm=v=>String(v||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
  let attempts=0;
  function apply(){
    attempts++;
    let vehicles;
    try{vehicles=state?.vehicles}catch{}
    if(!Array.isArray(vehicles)){
      if(attempts<80)setTimeout(apply,150);
      return;
    }
    let changed=false;
    for(const v of vehicles){
      const n=norm(v.name_full||v.name);
      const status=VERIFIED_STATUS.get(n);
      if(status&&v.production_status!==status){v.production_status=status;changed=true;}
    }
    if(changed){
      try{renderVehicles()}catch{}
      try{renderHangar()}catch{}
    }
    if(attempts<80)setTimeout(apply,250);
  }
  apply();
})();
