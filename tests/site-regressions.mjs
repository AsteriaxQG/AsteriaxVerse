import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {readBuilds,saveBuild,favorites} from '../website/loadout/storage.js';

const source=path=>fs.readFileSync(new URL('../'+path,import.meta.url),'utf8');
const nodes=new Map(),created=[];
class Element {
  constructor(){this.listeners={};this.dataset={};this.value='';this.hidden=false;this.isConnected=false;this.innerHTML='';this.classList={remove(){},toggle(){}};this.attributes={};}
  addEventListener(type,fn){(this.listeners[type]??=[]).push(fn)}
  setAttribute(name,value){this.attributes[name]=value}
  insertAdjacentElement(_,el){el.isConnected=true;nodes.set('#'+el.id,el)}
  querySelector(selector){return this.children?.[selector]||null}
  querySelectorAll(){return this.buttons||[]}
  contains(){return true}
  replaceChildren(){this.innerHTML=''}
  scrollIntoView(){}
}
for(const id of ['vehicleType','vehicleSearch','vehicleManufacturer','vehicleSort','vehicleGrid','vehicleCount','itemGrid','itemCount','itemSort'])nodes.set('#'+id,new Element());
const filters=new Element();nodes.set('#vehicles .filters',filters);
filters.appendChild=bar=>{filters.bar=bar;bar.children={};bar.buttons=['all','disponible','production','concept','gold-standard'].map(status=>{const btn=new Element();btn.dataset.shipStatus=status;btn.closest=()=>btn;bar.children['[data-count="'+status+'"]']=new Element();return btn})};
let mobile=true;
const breakpoint={get matches(){return mobile},addEventListener(_,fn){this.change=fn}};
const context={state:{vehicles:[],items:[]},window:{AsteriaxI18n:{isEnglish:()=>false},matchMedia:()=>breakpoint},document:{querySelector:s=>nodes.get(s)||null,createElement:()=>{const el=new Element();created.push(el);return el},head:{append(){},appendChild(){}}},renderVehicles(){},renderItems(){},bindCards(){},vehicleCard:v=>v.name+'|',itemCard:v=>v.name+'|'};
context.state.vehicles=Array.from({length:55},(_,i)=>({id:i,name:'Ship '+String(i).padStart(2,'0'),manufacturer:'RSI',production_status:'flight-ready',price_min:100-i,pledge_price:i+1}));
context.state.vehicles.push({name:'Concept',manufacturer:'RSI',production_status:'concept'},{name:'Production',manufacturer:'RSI',production_status:'active-production'});
vm.createContext(context);
vm.runInContext(source('website/vehiclefilters.js'),context);
vm.runInContext(source('website/performance.js'),context);
context.renderVehicles();
assert.match(nodes.get('#vehicleCount').textContent,/57 résultats/);
assert.equal(nodes.get('#vehicleGrid').innerHTML.split('|').length-1,24);
const choose=status=>{const btn=filters.bar.buttons.find(b=>b.dataset.shipStatus===status);filters.bar.listeners.click[0]({target:btn})};
choose('concept');assert.match(nodes.get('#vehicleCount').textContent,/1 résultat/);assert.equal(nodes.get('#vehicleGrid').innerHTML,'Concept|');
choose('production');assert.equal(nodes.get('#vehicleGrid').innerHTML,'Production|');
context.state.vehicles[0].catalog_gold_standard=true;
context.state.vehicles[1].catalog_gold_standard=false;
context.state.vehicles[2].catalog_gold_standard='true';
choose('gold-standard');assert.equal(nodes.get('#vehicleGrid').innerHTML,'Ship 00|');
assert.equal(filters.bar.children['[data-count="gold-standard"]'].textContent,1);
nodes.get('#vehicleSearch').value='Ship 01';context.renderVehicles();assert.match(nodes.get('#vehicleCount').textContent,/0 résultat/);
nodes.get('#vehicleSearch').value='';context.renderVehicles();
mobile=false;breakpoint.change();assert.equal(nodes.get('#vehicleGrid').innerHTML,'Ship 00|');
mobile=true;breakpoint.change();
choose('disponible');assert.match(nodes.get('#vehicleCount').textContent,/55 résultats/);
nodes.get('#vehicleSort').value='pledge-desc';nodes.get('#vehicleSort').listeners.change[0]();
assert.ok(nodes.get('#vehicleGrid').innerHTML.startsWith('Ship 54|'));
nodes.get('#vehicleSearch').value='Ship 01';context.renderVehicles();assert.equal(nodes.get('#vehicleGrid').innerHTML,'Ship 01|');
nodes.get('#vehicleSearch').value='';mobile=false;breakpoint.change();assert.equal(nodes.get('#vehicleGrid').innerHTML.split('|').length-1,48);
assert.equal(created.filter(e=>e.id==='vehiclePagination').length,1,'Pagination must have one owner');
assert.equal(nodes.get('#vehicleGrid').attributes['aria-busy'],'false');
context.window.AsteriaxLoadout={active:true};nodes.get('#itemGrid').innerHTML='untouched';context.renderItems();assert.equal(nodes.get('#itemGrid').innerHTML,'untouched');
context.window.AsteriaxLoadout.active=false;context.state.items=[{name:'Component'}];context.renderItems();assert.equal(nodes.get('#itemGrid').innerHTML,'Component|');

const shipSource=source('website/shipcatalog.js'),startup=shipSource.indexOf('function wait(){');
let refreshed=0;
const fields=new Map();
const ships={state:{db:{},vehicles:[{id:42,name:'Constellation Andromeda',url_photo:'https://example.org/ship.jpg'}],manufacturers:[],items:[]},window:{AsteriaxApi:{getJson:async()=>({ok:true,items:[{name:'Constellation Mk IV Andromeda',manufacturer:'RSI',status:'flight-ready',gold_standard:true,image:{id:'not-a-url',large:'https://example.org/new.jpg'}}]})}},document:{addEventListener(){},dispatchEvent(){},querySelector:s=>{if(!fields.has(s))fields.set(s,new Element());return fields.get(s)}},readStored:(_,fallback)=>fallback,imgUrl:String,writeStored(){},bindCards(){},renderVehicles(){},renderHangar(){},openVehicle(){},renderActiveCatalog(){refreshed++},setOptions(){},viewFromHash:()=> 'hangar',setTimeout(){},console,Event,CustomEvent:class{constructor(type,options){this.type=type;this.detail=options?.detail}},$:()=>new Element()};
vm.createContext(ships);
vm.runInContext(shipSource.slice(0,startup)+'globalThis.catalogTest={loadCatalog,maybeLoadCatalog,refreshNewestVehicleIds,newestVehicleIds,imageSource};})();',ships);
const catalog=ships.catalogTest;
catalog.refreshNewestVehicleIds(['42']);await catalog.loadCatalog();catalog.maybeLoadCatalog();
assert.equal(catalog.newestVehicleIds.has('42'),true,'Navigation must not clear verified new badges');
assert.equal(ships.state.vehicles[0].catalog_gold_standard,true);
assert.equal(ships.state.vehicles[0].catalog_image,'https://example.org/new.jpg');
assert.equal(refreshed,1,'An open Hangar must refresh after catalogue enrichment');
assert.equal(catalog.imageSource({id:'metadata',image:{name:'not-a-url',url:'https://example.org/actual.jpg'}}),'https://example.org/actual.jpg');
assert.equal(catalog.imageSource('javascript:alert(1)'),'');

const stored=new Map();globalThis.localStorage={getItem:key=>stored.get(key)||null,setItem:(key,value)=>stored.set(key,value)};
const valid={schema:1,id:'saved',name:'Test',shipId:'ship',patch:'4.10',slots:{}};
stored.set('ax_loadout_builds_v1',JSON.stringify([null,{},valid,5]));assert.deepEqual(readBuilds(),[valid]);saveBuild({...valid,name:'Updated'});assert.equal(readBuilds().length,1);
stored.set('ax_loadout_favorites_v1',JSON.stringify('not-an-array'));assert.equal(favorites().size,0);
stored.set('ax_loadout_favorites_v1',JSON.stringify([null,4,'component']));assert.deepEqual([...favorites()],['component']);
const handler=source('website/loadout/index.js'),saveStart=handler.indexOf(" if(action==='save'||action==='copySave')"),saveEnd=handler.indexOf(" if(action==='load')",saveStart);
const failedSave={action:'copySave',build:{...valid},crypto:{randomUUID:()=> 'copy'},validateBuild:b=>b,saveBuild(){throw Error('QuotaExceeded')},data:{}};
assert.throws(()=>vm.runInNewContext(handler.slice(saveStart,saveEnd),failedSave));assert.equal(failedSave.build.id,'saved');

const appSource=source('website/app.js'),optionsStart=appSource.indexOf('function setOptions('),optionsEnd=appSource.indexOf('const ITEM_SECTION_FR',optionsStart);
const optionsContext={esc:String,itemSectionLabel:String};vm.createContext(optionsContext);vm.runInContext(appSource.slice(optionsStart,optionsEnd),optionsContext);
const select={value:'RSI',set innerHTML(_){this.value=''}};optionsContext.setOptions(select,['RSI','Aegis'],'All');assert.equal(select.value,'RSI');optionsContext.setOptions(select,['Aegis'],'All');assert.equal(select.value,'');

const fixes=source('website/data-fixes.js'),fallbackStart=fixes.indexOf('  function namedFallback('),fallbackEnd=fixes.indexOf('  function run(',fallbackStart);
const unsafeName='<img src=x onerror=alert(1)>',box={dataset:{},matches:()=>true,closest:()=>({querySelector:()=>({textContent:unsafeName})}),querySelectorAll:()=>[],replaceChildren(...children){this.children=children},set innerHTML(_){throw Error('HTML parsing must not be used')}};
const fallbackContext={document:{createElement:()=>({})}};vm.createContext(fallbackContext);vm.runInContext(fixes.slice(fallbackStart,fallbackEnd),fallbackContext);fallbackContext.namedFallback(box);assert.equal(box.children[0].textContent,unsafeName);
console.log('PASS: integrated filters/sort/pagination, Builder isolation, catalogue refresh, badges, Gold Standard, image metadata, safe placeholders and local storage recovery');
