import assert from 'node:assert/strict';
import fs from 'node:fs';
import {compatible,createBuild,validateBuild,metrics,suggest,encodeBuild,decodeBuild} from '../website/loadout/core.js';
const data=JSON.parse(fs.readFileSync(new URL('../website/loadout/data/catalog.json',import.meta.url)));
for(const ship of data.ships){const b=createBuild(ship,data.patch);assert.deepEqual(validateBuild(b,data).slots,b.slots);assert.equal(new Set(ship.slots.map(s=>s.id)).size,ship.slots.length);for(const mode of ['dps','defense','quantum','pve','pvp'])assert.doesNotThrow(()=>validateBuild(suggest(b,data,mode),data))}
const ship=data.ships.find(s=>s.name==='RSI Constellation Andromeda'),build=createBuild(ship,data.patch),stock=metrics(build,data);
assert.ok(stock.dps>0);assert.ok(stock.shield>0);assert.ok(stock.cost>0);assert.ok(stock.unknown>0);
assert.deepEqual(decodeBuild(encodeBuild({...build,name:'Évasion ✧'}),data).slots,build.slots);
assert.throws(()=>validateBuild({...build,patch:'0.0'},data));assert.throws(()=>validateBuild({...build,slots:{...build.slots,unknown:'test'}},data));assert.throws(()=>decodeBuild('a'.repeat(80001),data));
const slot=ship.slots.find(s=>s.type==='Shield'),wrong=data.components.find(i=>i.type==='WeaponGun');assert.equal(compatible(slot,wrong),false);
const restricted={...slot,required:['nonexistent-tag']};assert.equal(compatible(restricted,data.components.find(i=>i.type==='Shield'&&i.id!==slot.stock&&i.size===slot.max)),false);
const fixed={...slot,editable:false};assert.equal(compatible(fixed,data.components.find(i=>i.type==='Shield'&&i.id!==slot.stock&&i.size===slot.max)),false);
const proposed=suggest(build,data,'dps');assert.ok(metrics(proposed,data).dps>=stock.dps);assert.deepEqual(build.slots,createBuild(ship,data.patch).slots);
console.log(`PASS: ${data.ships.length} stock builds, suggestions, size/type/tag/fixed compatibility, prices, import and share validation`);
