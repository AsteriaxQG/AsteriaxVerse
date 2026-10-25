import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const html=readFileSync(new URL('../website/index.html',import.meta.url),'utf8');
assert.match(html,/data-view="iae"/);
assert.match(html,/data-view="home"[^>]*>Accueil<\/button><button class="nav-btn iae-nav" data-view="iae"[^>]*>IAE<\/button>/);
assert.match(html,/id="iae" class="view/);
assert.match(html,/id="iaeFollowMain"/);
assert.match(html,/Calendrier prévisionnel · à confirmer par RSI/);
assert.match(html,/data-go="iae"/);
assert.match(html,/Programme prévisionnel · à confirmer/);
assert.match(html,/13 novembre à 17 h 00/);
assert.match(html,/16 h 00 UTC · à confirmer pour 2956/);
assert.match(html,/assets\/iae\/rental-schedule-full\.webp/);
assert.match(html,/assets\/iae\/floor-plan\.webp/);
assert.match(html,/assets\/iae\/manufacturers\.webp/);
assert.match(html,/<dialog id="iaeImageDialog"/);
assert.match(html,/class="iae-lightbox-stage"/);
assert.match(html,/data-iae-zoom-in/);
assert.match(html,/data-iae-zoom-out/);
assert.match(html,/data-iae-zoom-reset/);
assert.match(html,/data-iae-image/);
assert.doesNotMatch(html,/<a href="assets\/iae\/[^"]+" target="_blank"/);
assert.match(html,/RSI Constellation Mk V Andromeda/);
assert.match(html,/<li class="iae-ship-available"><a href="https:\/\/robertsspaceindustries\.com\/en\/pledge\/Standalone-Ships\/Constellation-Mk-V-Centaurus-Warbond"[^>]*><strong>RSI Skylark<\/strong>/);
assert.doesNotMatch(html.replace(/<[^>]*>/g,' '),/\bLEAK\b|\bdivulgué/i);
const code=readFileSync(new URL('../website/iae.js',import.meta.url),'utf8');
async function render(items){
  const grid={innerHTML:''},status={textContent:''},listeners={};
  const context={
    URL,location:{hash:'#iae'},
    setInterval(){},
    window:{AsteriaxI18n:{isEnglish:()=>false},AsteriaxApi:{getJson:async()=>({items})}},
    document:{querySelector:s=>s==='#iaeNewsGrid'?grid:s==='#iaeNewsStatus'?status:null,addEventListener:(name,fn)=>listeners[name]=fn}
  };
  vm.runInNewContext(code,context);
  await new Promise(resolve=>setImmediate(resolve));
  return{grid,status,listeners};
}
const old=await render([{title:'IAE 2955',publishedAt:'2025-11-20',url:'https://robertsspaceindustries.com/en/comm-link/old'}]);
assert.equal(old.grid.innerHTML,'');
assert.match(old.status.textContent,/informations à venir/);
const current=await render([{title:'IAE 2956',publishedAt:'2026-11-01',url:'https://robertsspaceindustries.com/en/comm-link/new'},{title:'IAE 2956',publishedAt:'2026-11-01',url:'https://example.com/malicious'}]);
assert.match(current.grid.innerHTML,/IAE 2956/);
assert.doesNotMatch(current.grid.innerHTML,/example\.com/);
assert.match(current.status.textContent,/1 annonce/);
const image={src:'',alt:'',style:{},clientWidth:800,clientHeight:600},handlers={},documentHandlers={},dialogHandlers={},stageHandlers={},level={textContent:''};
const button=name=>({addEventListener:(event,fn)=>handlers[name]=fn});
const stage={clientWidth:800,clientHeight:600,addEventListener:(event,fn)=>stageHandlers[event]=fn,setPointerCapture(){},classList:{add(){},remove(){}}};
const controls={'.iae-lightbox-stage':stage,img:image,'[data-iae-zoom-level]':level,'[data-iae-zoom-in]':button('in'),'[data-iae-zoom-out]':button('out'),'[data-iae-zoom-reset]':button('reset'),'.iae-lightbox-close':button('closeButton')};
const dialog={showModal(){handlers.opened=true},close(){handlers.closed=true},querySelector:s=>controls[s],addEventListener:(name,fn)=>dialogHandlers[name]=fn};
const link={href:'https://asteriaxverse.fr/assets/iae/floor-plan.webp',querySelector:()=>({alt:'Plan IAE'})};
vm.runInNewContext(code,{
  URL,location:{hash:''},
  setInterval(){},
  window:{AsteriaxI18n:{isEnglish:()=>false}},
  document:{querySelector:s=>s==='#iaeImageDialog'?dialog:s==='#iaeImageDialog img'?image:null,addEventListener:(name,fn)=>documentHandlers[name]=fn}
});
let prevented=false;
documentHandlers.click({target:{closest:()=>link},preventDefault(){prevented=true}});
assert.equal(prevented,true);
assert.equal(image.src,link.href);
assert.equal(image.alt,'Plan IAE');
assert.equal(handlers.opened,true);
handlers.in();assert.equal(level.textContent,'150 %');
stageHandlers.wheel({deltaY:-1,preventDefault(){prevented=true}});assert.equal(level.textContent,'180 %');
handlers.reset();assert.equal(level.textContent,'100 %');
handlers.closeButton();
assert.equal(handlers.closed,true);
handlers.closed=false;
dialogHandlers.click({target:dialog});
assert.equal(handlers.closed,true);
function followAt(time){
  const label={textContent:''},main={textContent:''},next={textContent:''};
  class ClockDate extends Date{static now(){return time}}
  vm.runInNewContext(code,{
    URL,Date:ClockDate,location:{hash:''},setInterval(){},
    window:{AsteriaxI18n:{isEnglish:()=>false}},
    document:{querySelector:s=>({'#iaeFollowLabel':label,'#iaeFollowMain':main,'#iaeFollowNext':next})[s]||null,addEventListener(){} }
  });
  return{label:label.textContent,main:main.textContent,next:next.textContent};
}
assert.match(followAt(Date.UTC(2026,10,13,15,59)).main,/1 min/);
assert.equal(followAt(Date.UTC(2026,10,13,16)).main,'RSI');
assert.equal(followAt(Date.UTC(2026,10,14,16)).main,'Origin');
assert.equal(followAt(Date.UTC(2026,10,30,16)).main,'Événement terminé');
console.log('PASS: IAE navigation, pending information, current-year announcements and official link validation');
