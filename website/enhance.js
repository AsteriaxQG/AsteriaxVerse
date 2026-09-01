(()=>{
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
function num(t){const n=String(t||'').replace(/[^0-9.,-]/g,'').replace(/\s/g,'').replace(',','.');return Number(n)||0}
function sortGrid(grid,type){if(!grid)return;const cards=[...grid.children];cards.sort((a,b)=>{const name=x=>(x.querySelector('h3')?.textContent||'').trim();const price=x=>num(x.querySelector('.price')?.textContent);if(type==='price')return price(a)-price(b);if(type==='price-desc')return price(b)-price(a);if(type==='scu'){const vals=x=>[...x.querySelectorAll('.card-meta>div')].find(d=>d.querySelector('span')?.textContent.trim()==='SCU')?.querySelector('strong')?.textContent;return num(vals(b))-num(vals(a))}return name(a).localeCompare(name(b),'fr',{numeric:true})});cards.forEach(c=>grid.appendChild(c))}
function bindSort(id,grid){const s=$(id),g=$(grid);if(!s||!g)return;s.addEventListener('change',()=>sortGrid(g,s.value))}
bindSort('#vehicleSort','#vehicleGrid');bindSort('#itemSort','#itemGrid');
const hg=$('#hangarGrid');function hangarFilter(v){if(!hg)return;[...hg.children].forEach(c=>c.hidden=v==='ships'?!c.classList.contains('ship-card'):v==='items'?!c.classList.contains('item-card'):false)}
$$('[data-hangar-filter]').forEach(b=>b.addEventListener('click',()=>{$$('[data-hangar-filter]').forEach(x=>x.classList.remove('active'));b.classList.add('active');hangarFilter(b.dataset.hangarFilter)}));if(hg)new MutationObserver(()=>{const a=$('[data-hangar-filter].active');if(a)hangarFilter(a.dataset.hangarFilter)}).observe(hg,{childList:true});
$$('.nav-btn').forEach(b=>b.addEventListener('click',()=>{const label=b.textContent.replace('★','').trim();document.title=b.dataset.view==='home'?'AsteriaxVerse':`${label} · AsteriaxVerse`}));
document.addEventListener('keydown',e=>{if(e.key==='/'&&!/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)){e.preventDefault();$('#globalSearch')?.focus()}});
})();