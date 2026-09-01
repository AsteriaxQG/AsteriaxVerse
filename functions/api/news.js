const RSI='https://robertsspaceindustries.com';
const SOURCES=[
  `${RSI}/en/patch-notes`,
  `${RSI}/en/comm-link/transmission/star-citizen`
];

function decode(s=''){
  return s.replace(/&nbsp;/g,' ').replace(/&amp;/g,'&').replace(/&quot;/g,'"').replace(/&#39;|&apos;/g,"'").replace(/&lt;/g,'<').replace(/&gt;/g,'>');
}
function cleanHtml(s=''){
  return decode(s.replace(/<script[\s\S]*?<\/script>/gi,' ').replace(/<style[\s\S]*?<\/style>/gi,' ').replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim());
}
function absolute(href=''){
  if(!href)return'';
  if(/^https?:\/\//i.test(href))return href;
  const path=href.startsWith('/')?href:`/${href}`;
  return `${RSI}${path.replace(/^\/comm-link\//i,'/en/comm-link/')}`;
}
function category(title,url,raw=''){
  const s=`${title} ${url} ${raw}`.toLowerCase();
  if(s.includes('/patch-notes/')||s.includes('patch notes')||/star citizen alpha \d/.test(s))return'PATCH';
  if(s.includes('sneak peek'))return'SNEAK PEEK';
  if(s.includes('roadmap roundup')||s.includes('roadmap'))return'ROADMAP';
  if(s.includes('inside star citizen')||s.includes('star citizen live')||s.includes('behind the ships')||s.includes('video'))return'VIDEO';
  if(s.includes('known issue'))return'KNOWN ISSUE';
  return'NEWS';
}
function parseTitle(inner=''){
  const heading=inner.match(/<h[1-6][^>]*>([\s\S]*?)<\/h[1-6]>/i);
  if(heading){const t=cleanHtml(heading[1]);if(t)return t;}
  return cleanHtml(inner).replace(/^(post|video|patchnotes)\s+/i,'').replace(/\s+0\s+Posted:\s*[\s\S]*$/i,'').trim();
}
function parsePosted(inner=''){
  const text=cleanHtml(inner);
  const m=text.match(/Posted:\s*((?:\d+|an?|one)\s+(?:minute|hour|day|week|month|year)s?\s+ago)/i);
  return m?m[1]:'';
}
function parseExcerpt(inner='',title=''){
  let text=cleanHtml(inner).replace(/^(post|video|patchnotes)\s+/i,'').trim();
  if(title&&text.toLowerCase().startsWith(title.toLowerCase()))text=text.slice(title.length).trim();
  text=text.replace(/^0\s*/,'').replace(/^Posted:\s*(?:\d+|an?|one)\s+(?:minute|hour|day|week|month|year)s?\s+ago\s*/i,'').trim();
  if(!text||text===title)return'';
  return text.length>220?text.slice(0,217).trim()+'…':text;
}
function parseArticles(html,forcePatch=false){
  const out=[];
  const seen=new Set();
  const re=/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi;
  let m;
  while((m=re.exec(html))){
    const href=m[1];
    if(!/\/comm-link\/(?:Patch-Notes|patch-notes|transmission|engineering|citizens|spectrum-dispatch|serialized-fiction)\/\d+-/i.test(href))continue;
    const url=absolute(href);
    if(seen.has(url))continue;
    const title=parseTitle(m[2]);
    if(!title||title.length<4||title.length>180)continue;
    seen.add(url);
    out.push({title,url,category:forcePatch?'PATCH':category(title,url,m[2]),posted:parsePosted(m[2]),excerpt:parseExcerpt(m[2],title)});
  }
  return out;
}
async function fetchSource(url){
  const r=await fetch(url,{headers:{'User-Agent':'AsteriaxVerse/1.0 (+https://asteriaxverse.pages.dev)','Accept':'text/html,application/xhtml+xml'}});
  if(!r.ok)throw new Error(`RSI ${r.status}`);
  return r.text();
}
function fallback(){
  return [
    {title:'Patch Notes Star Citizen',url:`${RSI}/en/patch-notes`,category:'PATCH',posted:'',excerpt:'Accéder aux dernières notes de mise à jour officielles.'},
    {title:'Dernières actualités Star Citizen',url:`${RSI}/en/comm-link/transmission/star-citizen`,category:'NEWS',posted:'',excerpt:'Actualités officielles RSI, événements et annonces du Verse.'},
    {title:'Development Hub',url:`${RSI}/en/development`,category:'ROADMAP',posted:'',excerpt:'Roadmap et informations de développement officielles.'}
  ];
}

export async function onRequestGet(context){
  const cache=caches.default;
  const cacheKey=new Request(new URL('/api/news?cache=v2',context.request.url).toString(),{method:'GET'});
  const cached=await cache.match(cacheKey);
  if(cached)return cached;
  let items=[];
  let live=true;
  try{
    const [patchHtml,commHtml]=await Promise.all(SOURCES.map(fetchSource));
    const patches=parseArticles(patchHtml,true).slice(0,4);
    const comm=parseArticles(commHtml,false).slice(0,16);
    const dedup=new Map();
    [...patches,...comm].forEach(x=>dedup.set(x.url,x));
    items=[...dedup.values()].slice(0,18);
    if(!items.length)throw new Error('Aucune actualité RSI détectée');
  }catch(err){
    console.error('AsteriaxVerse news:',err);
    live=false;
    items=fallback();
  }
  const payload=JSON.stringify({ok:true,live,updatedAt:new Date().toISOString(),refreshSeconds:3600,source:'Roberts Space Industries',items});
  const response=new Response(payload,{headers:{'content-type':'application/json; charset=utf-8','cache-control':'public, max-age=300, s-maxage=3600, stale-while-revalidate=86400','access-control-allow-origin':'*'}});
  context.waitUntil(cache.put(cacheKey,response.clone()));
  return response;
}
