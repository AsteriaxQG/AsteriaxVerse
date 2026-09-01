const RSI='https://robertsspaceindustries.com';

function clean(s){return String(s||'').replace(/\s+/g,' ').trim()}
function absolute(href){if(!href)return'';if(href.startsWith('http'))return href;return RSI+href}
function category(title,href=''){
  const t=(title+' '+href).toLowerCase();
  if(t.includes('patch')||href.includes('/patch-notes'))return'PATCH';
  if(t.includes('roadmap'))return'ROADMAP';
  if(t.includes('sneak peek')||t.includes('sneak-peek'))return'SNEAK PEEK';
  if(t.includes('star citizen live')||t.includes('inside star citizen')||t.includes('behind the ships'))return'VIDEO';
  if(t.includes('known issue'))return'KNOWN ISSUE';
  return'NEWS';
}

async function linksFrom(url,match){
  const res=await fetch(url,{headers:{'User-Agent':'AsteriaxVerse/1.0 (+https://asteriaxverse.pages.dev)','Accept':'text/html'}});
  if(!res.ok)throw new Error(`RSI ${res.status}`);
  const html=await res.text();
  const out=[];
  const re=/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi;
  let m;
  while((m=re.exec(html))){
    const href=m[1];
    if(!match(href))continue;
    const title=clean(m[2].replace(/<[^>]+>/g,' ').replace(/&amp;/g,'&').replace(/&#39;/g,"'").replace(/&quot;/g,'"').replace(/&nbsp;/g,' '));
    if(title.length<5)continue;
    out.push({title,url:absolute(href),category:category(title,href)});
  }
  return out;
}

function unique(items){
  const seen=new Set();
  return items.filter(x=>{const k=x.url+'|'+x.title.toLowerCase();if(seen.has(k))return false;seen.add(k);return true});
}

export async function onRequestGet(context){
  const cache=caches.default;
  const key=new Request(new URL(context.request.url).origin+'/api/news?cache=v1');
  const hit=await cache.match(key);
  if(hit)return hit;
  try{
    const [comm,patch]=await Promise.all([
      linksFrom(`${RSI}/en/comm-link/transmission/star-citizen`,h=>h.includes('/en/comm-link/')&&!h.endsWith('/en/comm-link/')),
      linksFrom(`${RSI}/en/patch-notes`,h=>h.includes('/en/patch-notes/'))
    ]);
    let items=unique([...patch,...comm]);
    items.sort((a,b)=>{
      const weight={PATCH:0,ROADMAP:1,'SNEAK PEEK':2,VIDEO:3,NEWS:4,'KNOWN ISSUE':5};
      return (weight[a.category]??9)-(weight[b.category]??9);
    });
    items=items.slice(0,18);
    const body=JSON.stringify({ok:true,updatedAt:new Date().toISOString(),source:'Roberts Space Industries',items});
    const response=new Response(body,{headers:{'content-type':'application/json; charset=utf-8','cache-control':'public, max-age=300, s-maxage=1800','access-control-allow-origin':'*'}});
    context.waitUntil(cache.put(key,response.clone()));
    return response;
  }catch(error){
    return Response.json({ok:false,error:'RSI temporairement indisponible',items:[]},{status:502,headers:{'cache-control':'no-store'}});
  }
}
