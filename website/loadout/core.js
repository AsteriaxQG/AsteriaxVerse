export const families={WeaponGun:['Armes','Weapons','⌖'],Missile:['Missiles','Missiles','↗'],Shield:['Boucliers','Shields','◇'],QuantumDrive:['Propulsion quantique','Quantum drive','✧'],PowerPlant:['Centrales','Power plants','ϟ'],Cooler:['Refroidisseurs','Coolers','❄'],WeaponMining:['Lasers de minage','Mining lasers','⛏'],TractorBeam:['Rayons tracteurs','Tractor beams','⊕']};
export function compatible(slot,item){
 if(!slot||!item)return false;
 if(item.id===slot.stock)return true;
 if(!slot.editable||!Number.isFinite(slot.min)||!Number.isFinite(slot.max)||item.size<slot.min||item.size>slot.max)return false;
 const typeMatch=slot.types.some(t=>t.Type===item.type&&(!t.SubTypes?.length||t.SubTypes.includes(item.subType)||item.type==='QuantumDrive'&&item.subType==='UNDEFINED'&&t.SubTypes.includes('QDrive')));
 return typeMatch&&slot.required.every(tag=>item.tags.includes(tag));
}
export function createBuild(ship,patch){return {schema:1,id:crypto.randomUUID(),name:ship.name,shipId:ship.id,patch,slots:Object.fromEntries(ship.slots.map(s=>[s.id,s.stock])),updatedAt:new Date().toISOString()}}
export function validateBuild(input,data){
 if(!input||input.schema!==1||typeof input.name!=='string'||input.name.length>120||input.patch!==data.patch||!input.slots||typeof input.slots!=='object'||Array.isArray(input.slots))throw Error('invalidBuild');
 const ship=data.ships.find(s=>s.id===input.shipId);if(!ship)throw Error('invalidBuild');
 const validIds=new Set(ship.slots.map(s=>s.id));if(Object.keys(input.slots).some(k=>!validIds.has(k)))throw Error('invalidBuild');
 const slots={};for(const slot of ship.slots){const id=input.slots[slot.id];if(id===undefined)throw Error('invalidBuild');if(id===null){if(!slot.editable&&slot.stock)throw Error('invalidBuild')}else if(!compatible(slot,data.components.find(i=>i.id===id)))throw Error('invalidBuild');slots[slot.id]=id}
 return {schema:1,id:typeof input.id==='string'&&/^[a-f0-9-]{36}$/.test(input.id)?input.id:crypto.randomUUID(),name:input.name,shipId:ship.id,patch:data.patch,slots,updatedAt:typeof input.updatedAt==='string'?input.updatedAt:new Date().toISOString()};
}
export function metrics(build,data){
 const byId=new Map(data.components.map(i=>[i.id,i])),items=Object.values(build.slots).filter(Boolean).map(id=>byId.get(id)).filter(Boolean);
 const sum=(type,key)=>{const a=items.filter(i=>i.type===type);return !a.length?0:a.some(i=>!Number.isFinite(i.stats[key]))?null:a.reduce((n,i)=>n+i.stats[key],0)};
 const quantum=items.find(i=>i.type==='QuantumDrive');let cost=0,unknown=0;
 for(const i of items){if(i.offers.length)cost+=i.offers[0].price;else unknown++}
 const missingStock=data.ships.find(s=>s.id===build.shipId).slots.filter(s=>!s.stock&&s.stockName).length;
 return {dps:sum('WeaponGun','dps'),shield:sum('Shield','shield'),regen:sum('Shield','regen'),power:sum('PowerPlant','power'),cooling:sum('Cooler','cooling'),speed:quantum?.stats.speed??null,spool:quantum?.stats.spool??null,cost,unknown:unknown+missingStock,items};
}
export function suggest(build,data,mode){
 const ship=data.ships.find(s=>s.id===build.shipId),next=structuredClone(build);
 const score=i=>mode==='dps'?(i.type==='WeaponGun'?i.stats.dps:null):mode==='defense'?(i.type==='Shield'?i.stats.shield:null):mode==='quantum'?(i.type==='QuantumDrive'?i.stats.speed:null):mode==='pvp'?(i.type==='WeaponGun'?i.stats.dps:i.type==='Shield'?i.stats.shield:null):(i.type==='WeaponGun'?i.stats.dps:i.type==='Shield'?i.stats.shield:i.type==='QuantumDrive'&&i.stats.fuel>0?1/i.stats.fuel:null);
 for(const s of ship.slots){if(!s.editable)continue;const candidates=data.components.filter(i=>compatible(s,i)&&Number.isFinite(score(i))).sort((a,b)=>score(b)-score(a)||a.name.localeCompare(b.name));if(candidates.length)next.slots[s.id]=candidates[0].id}
 return next;
}
export function encodeBuild(build){return btoa(String.fromCharCode(...new TextEncoder().encode(JSON.stringify(build)))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'')}
export function decodeBuild(value,data){if(value.length>80000)throw Error('invalidBuild');return validateBuild(JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(value.replace(/-/g,'+').replace(/_/g,'/')),c=>c.charCodeAt(0)))),data)}
