import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const html=readFileSync(new URL('../website/index.html',import.meta.url),'utf8');
assert.match(html,/data-view="iae"/);
assert.match(html,/id="iae" class="view/);
assert.match(html,/data-go="iae"/);
const code=readFileSync(new URL('../website/iae.js',import.meta.url),'utf8');
async function render(items){
  const grid={innerHTML:''},status={textContent:''},listeners={};
  const context={
    URL,location:{hash:'#iae'},
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
console.log('PASS: IAE navigation, pending information, current-year announcements and official link validation');
