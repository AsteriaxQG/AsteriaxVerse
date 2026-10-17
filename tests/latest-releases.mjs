import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source=fs.readFileSync(new URL('../website/home.js',import.meta.url),'utf8');
const boot=source.indexOf("  q('#homePlayers')?.closest('div')?.remove();");
assert.ok(boot>0,'Home startup marker must be present');
const grid={innerHTML:''},events=[],state={vehicles:[]};
const context={
  URL,state,
  document:{querySelector:selector=>selector==='#homeShipGrid'?grid:null,dispatchEvent:event=>events.push(event)},
  vehicleCard:ship=>'<article>'+ship.name+'</article>',
  CustomEvent:class{constructor(type,options){this.type=type;this.detail=options.detail}}
};
vm.runInNewContext(source.slice(0,boot)+`
  globalThis.testReleases={
    set(ships,news){shipFeed=ships;homeNewsItems=news;state.vehicles=ships.map(ship=>({...ship,id:ship.id||ship.name}));},
    pick:pickFeaturedShips,render:renderFeaturedShips
  };
})();`,context);
const api=context.testReleases;
const centaurus={id:'rsi-325',name:'Constellation Mk V Centaurus',status:'flight-ready'};
const announcement={
  title:'RSI Constellation Mk V Centaurus - For Living Out There',
  excerpt:'RSI carries its legacy into the future with the next generation of one of space travel’s most iconic and beloved ships.',
  url:'https://robertsspaceindustries.com/comm-link/transmission/21335-RSI-Constellation-Mk-V-Centaurus'
};
const qa={...announcement,title:'Q&A: RSI Constellation Mk V Centaurus',url:'https://robertsspaceindustries.com/comm-link/engineering/21377-Q-A-RSI-Constellation-Mk-V-Centaurus'};
const video={...announcement,title:'Star Citizen | Behind the Ships: RSI Constellation Mk V Centaurus : Video',url:'https://robertsspaceindustries.com/comm-link/transmission/21381-Star-Citizen-Behind-The-Ships-RSI-Constellation-Mk-V-Centaurus-Video'};
const names=()=>Array.from(api.pick(),ship=>ship.name);
api.set([centaurus,{name:'Constellation Mk IV Andromeda',status:'flight-ready'}],[video,qa,announcement]);
assert.deepEqual(names(),[centaurus.name],'A marketing-slogan launch must select Centaurus without selecting Mk IV');
api.render();
assert.match(grid.innerHTML,/Constellation Mk V Centaurus/);
assert.deepEqual(Array.from(events.at(-1).detail.ids),['rsi-325'],'New badge must follow the featured release');

api.set([centaurus],[video,qa]);
assert.deepEqual(names(),[],'A Q&A or Behind the Ships video alone is not a release announcement');
api.set([{...centaurus,status:'in-concept'}],[announcement]);
assert.deepEqual(names(),[],'Concept announcements must not be displayed as released');
api.set([centaurus],[{...announcement,url:'https://example.test/comm-link/transmission/21335-RSI-Constellation-Mk-V-Centaurus'}]);
assert.deepEqual(names(),[],'Only RSI announcements are trusted');
api.set([centaurus],[{...announcement,title:'Constellation Mk V Centaurus balance changes',url:'https://robertsspaceindustries.com/comm-link/transmission/12345-Balance-Changes'}]);
assert.deepEqual(names(),[],'An ordinary balance article must not be treated as a launch');

const next={name:'Mirai Future Test',status:'flight-ready'};
const nextAnnouncement={title:'Mirai Future Test - Explore Further',excerpt:'A new horizon.',url:'https://robertsspaceindustries.com/en/comm-link/transmission/99999-Mirai-Future-Test'};
api.set([centaurus,next],[nextAnnouncement,announcement]);
assert.deepEqual(names(),[next.name],'A later product launch must automatically replace the previous batch');
const ground={name:'Argo ATLS IKTI Akuma',status:'flight-ready',type:'Ground',size:'Vehicle'};
const raven={name:'Aegis Sabre Raven EX',status:'flight-ready'};
api.set([{name:'Aegis Sabre',status:'flight-ready'},{name:'Aegis Sabre Raven',status:'flight-ready'},raven,ground],[
  {title:'Aegis Sabre Raven EX and Argo ATLS IKTI Akuma - Available now',url:'https://robertsspaceindustries.com/comm-link/transmission/99998-New-Releases',excerpt:''}
]);
assert.deepEqual(names().sort(),[raven.name,ground.name].sort(),'A release batch includes vehicles and excludes base variants');
api.set([centaurus],[{...announcement,title:'RSI Constellation Mk V Centaurus | Star Citizen',url:'https://robertsspaceindustries.com/en/comm-link/transmission/21335-RSI-Constellation-Mk-V-Centaurus'}]);
assert.deepEqual(names(),[centaurus.name],'Archived RSI product announcements must still identify the latest release');
console.log('PASS: actual RSI Centaurus launch, archive feed, latest-only batches, vehicles, new badges and false-positive exclusions');
