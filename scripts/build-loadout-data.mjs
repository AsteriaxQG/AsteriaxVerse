import fs from 'node:fs';
import path from 'node:path';
import {DatabaseSync} from 'node:sqlite';
// Inputs are pinned exports, downloaded separately. No network request runs in the site.
const [shipsFile,itemsFile]=process.argv.slice(2);
if(!shipsFile||!itemsFile)throw Error('Usage: node scripts/build-loadout-data.mjs ships.json ship-items.json');
const rawShips=JSON.parse(fs.readFileSync(shipsFile)),rawItems=JSON.parse(fs.readFileSync(itemsFile));
const db=new DatabaseSync('data/asteriax_sc.db',{readOnly:true});
const dbItems=db.prepare('SELECT id,uuid,name,game_version FROM items').all();
const dbShips=db.prepare('SELECT * FROM vehicles').all();
const offers=db.prepare('SELECT o.item_id,o.price_buy,t.name,t.star_system,t.planet,t.city,t.space_station,t.outpost,t.date_modified,t.game_version FROM item_offers o JOIN terminals t ON t.id=o.terminal_id WHERE o.price_buy>0 ORDER BY o.price_buy').all();
const types=new Set(['WeaponGun','Missile','Shield','QuantumDrive','PowerPlant','Cooler','WeaponMining','TractorBeam']);
const norm=s=>String(s||'').toLowerCase().replace(/[^a-z0-9]/g,'');
const number=n=>Number.isFinite(n)?n:null;
const components=rawItems.filter(i=>types.has(i.type)&&i.stdItem&&i.name&&!i.name.includes('PLACEHOLDER')).map(i=>{
 const s=i.stdItem,match=dbItems.find(x=>x.uuid?.toLowerCase()===i.reference?.toLowerCase());
 const deltas=s.ResourceNetwork?.States?.flatMap(x=>x.Deltas||[])||[];
 const generation=resource=>{const a=deltas.filter(d=>d.Type==='Generation'&&d.Resource===resource||d.Type==='Conversion'&&d.GeneratedResource===resource).map(d=>d.GeneratedResource===resource?d.GeneratedRate:d.Rate).filter(Number.isFinite);return a.length?Math.max(...a):null};
 return {id:i.reference,name:i.name,type:i.type,subType:i.subType,size:i.size,grade:s.DescriptionData?.Grade||null,manufacturer:s.Manufacturer?.Name||i.manufacturer||'',tags:[...new Set([...(s.Tags||[]),...(i.entity_tag_map||[]).map(t=>t.name)])],className:i.className,
 stats:{dps:number(s.Weapon?.Damage?.DpsTotal),range:number(s.Weapon?.EffectiveRange),shield:number(s.Shield?.MaxShieldHealth),regen:number(s.Shield?.MaxShieldRegen),speed:number(s.QuantumDrive?.StandardJump?.DriveSpeed),spool:number(s.QuantumDrive?.StandardJump?.SpoolUpTime),fuel:number(s.QuantumDrive?.FuelConsumptionSCUPerGM),power:generation('Power'),cooling:generation('Coolant'),draw:number(s.ResourceNetwork?.Usage?.Power?.Maximum),missile:number(s.Missile?.DamageTotal)},
 offers:match?offers.filter(o=>o.item_id===match.id).map(o=>({price:o.price_buy,location:[o.star_system,o.planet,o.city||o.space_station||o.outpost,o.name].filter(Boolean).join(' › '),patch:o.game_version||null,updated:o.date_modified||null})):[]};
});
const ids=new Set(components.map(i=>i.id));
const ships=rawShips.filter(s=>s.IsSpaceship&&s.Loadout&&!/ballista.*(dunestalker|snowblind)/i.test(s.Name)&&!/_GS$/.test(s.ClassName)).filter((s,_,all)=>!all.some(other=>other.Name===s.Name&&other.ClassName.length<s.ClassName.length)).map(s=>{
 const slots=[];function visit(p){const type=(p.Type||'').split('.')[0],accepted=(p.CompatibleTypes||[]).filter(t=>types.has(t.Type));
 if(types.has(type)||!p.Type&&accepted.length){slots.push({id:(p.Path||[p.HardpointName]).join('/'),label:p.HardpointName,type:types.has(type)?type:accepted[0].Type,types:accepted,min:p.MinSize,max:p.MaxSize,editable:p.Editable===true,required:p.RequiredTags||[],portTags:p.PortTags||[],stock:ids.has(p.UUID)?p.UUID:null,stockName:p.Name||null});}
 (p.Loadout||[]).forEach(visit)}s.Loadout.forEach(visit);
 const match=dbShips.find(v=>v.uuid?.toLowerCase()===s.UUID?.toLowerCase())||dbShips.find(v=>norm(v.name_full)===norm(s.Name)||norm(v.name)===norm(s.Name));
 return {id:s.UUID,name:s.Name,manufacturer:s.Manufacturer?.Name||'',role:s.Role||'',length:s.Length,width:s.Width,height:s.Height,crew:s.Crew,scu:s.Cargo,photo:match?.url_photo||null,catalogId:match?.id||null,slots};
}).filter(s=>s.slots.length).sort((a,b)=>a.name.localeCompare(b.name));
const patch=process.env.AX_LOADOUT_PATCH||'4.10.0-LIVE.12519617';
const revision=process.env.AX_LOADOUT_REVISION||'f6a2b29e77aaa2c824aa4fd1c0478c8058c69fca';
if(!/^\d+\.\d+\.\d+-(?:LIVE|PTU|EPTU)\.\d+$/i.test(patch)||!/^[a-f0-9]{40}$/i.test(revision))throw Error('Invalid patch provenance');
if(ships.length<150||components.length<300)throw Error('Source validation failed: refusing an incomplete catalogue');
const out={schema:1,patch,source:'https://github.com/StarCitizenWiki/scunpacked-data',revision,generatedAt:new Date().toISOString(),ships,components};
fs.mkdirSync('website/loadout/data',{recursive:true});fs.writeFileSync('website/loadout/data/catalog.json',JSON.stringify(out));
console.log(JSON.stringify({ships:ships.length,components:components.length,priced:components.filter(i=>i.offers.length).length,bytes:fs.statSync('website/loadout/data/catalog.json').size}));
