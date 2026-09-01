const API='https://api.star-citizen.wiki/api/shipmatrix/vehicles';
const RSI='https://robertsspaceindustries.com';

function textValue(v,depth=0){
  if(v===null||v===undefined||depth>4)return'';
  if(typeof v==='string'||typeof v==='number'||typeof v==='boolean')return String(v).trim();
  if(Array.isArray(v))return v.map(x=>textValue(x,depth+1)).find(Boolean)||'';
  if(typeof v==='object'){
    for(const k of ['name','display_name','label','value','title','code','slug','status','type','size']){
      const t=textValue(v[k],depth+1);if(t)return t;
    }
  }
  return'';
}
function firstUrl(v,depth=0){
  if(v===null||v===undefined||depth>6)return'';
  if(typeof v==='string'){
    const s=v.trim();
    if(/^https?:\/\//i.test(s)||s.startsWith('//'))return s.startsWith('//')?'https:'+s:s;
    if(/^\/(?:media|i|images|rsi|assets)\//i.test(s))return `${RSI}${s}`;
    return'';
  }
  if(Array.isArray(v)){for(const x of v){const u=firstUrl(x,depth+1);if(u)return u}return''}
  if(typeof v==='object'){
    for(const k of ['source_url','slideshow_wide','hub_large','post','large','medium','small','thumbnail','image','url','src','images','media']){
      const u=firstUrl(v[k],depth+1);if(u)return u;
    }
    for(const x of Object.values(v)){const u=firstUrl(x,depth+1);if(u)return u}
  }
  return'';
}
function normalizeStatus(v){
  const s=textValue(v).toLowerCase().replace(/_/g,'-').replace(/\s+/g,'-');
  const aliases={'flightready':'flight-ready','flight-ready':'flight-ready','inconcept':'in-concept','in-concept':'in-concept','concept':'concept','activeproduction':'active-production','active-production':'active-production','longtermproduction':'long-term-production','long-term-production':'long-term-production','hangarready':'hangar-ready','hangar-ready':'hangar-ready'};
  return aliases[s.replace(/-/g,'')]||aliases[s]||s||'unknown';
}
function normalize(v){
  const manufacturer=textValue(v.manufacturer)||textValue(v.manufacturer_name);
  const image=firstUrl(v.media)||firstUrl(v.image)||firstUrl(v.images);
  return {
    rsi_id:textValue(v.id),
    name:textValue(v.name),
    manufacturer,
    status:normalizeStatus(v.production_status),
    status_note:textValue(v.production_note),
    focus:textValue(v.focus),
    type:textValue(v.type),
    size:textValue(v.size),
    scu:v.cargocapacity??null,
    crew_min:v.min_crew??null,
    crew_max:v.max_crew??null,
    length:v.length??null,
    beam:v.beam??null,
    height:v.height??null,
    msrp:v.msrp??null,
    description:textValue(v.description),
    image,
    rsi_url:v.url?`${RSI}${String(v.url).startsWith('/')?v.url:'/'+v.url}`:'',
    updated:textValue(v.time_modified)
  };
}

export async function onRequestGet(context){
  const cache=caches.default;
  const key=new Request(new URL('/api/ships?catalog=v2',context.request.url).toString());
  const cached=await cache.match(key);
  if(cached)return cached;
  try{
    const url=`${API}?page%5Bsize%5D=200&sort=name`;
    const r=await fetch(url,{headers:{Accept:'application/json','User-Agent':'AsteriaxVerse/1.1'}});
    if(!r.ok)throw new Error(`Ship Matrix API ${r.status}`);
    const json=await r.json();
    let data=Array.isArray(json.data)?json.data:[];
    const pages=Number(json.meta?.last_page||1);
    if(pages>1){
      const rest=await Promise.all(Array.from({length:pages-1},(_,i)=>fetch(`${API}?page%5Bsize%5D=200&page%5Bnumber%5D=${i+2}&sort=name`,{headers:{Accept:'application/json','User-Agent':'AsteriaxVerse/1.1'}}).then(x=>x.ok?x.json():{data:[]})));
      rest.forEach(x=>{if(Array.isArray(x.data))data.push(...x.data)});
    }
    const items=data.map(normalize).filter(x=>x.name);
    const response=new Response(JSON.stringify({ok:true,source:'RSI Ship Matrix via Star Citizen Wiki API',updatedAt:new Date().toISOString(),items}),{headers:{'content-type':'application/json; charset=utf-8','cache-control':'public, max-age=120, s-maxage=3600, stale-while-revalidate=21600','access-control-allow-origin':'*'}});
    context.waitUntil(cache.put(key,response.clone()));
    return response;
  }catch(error){
    return new Response(JSON.stringify({ok:false,error:String(error?.message||error),items:[]}),{status:502,headers:{'content-type':'application/json; charset=utf-8','cache-control':'no-store'}});
  }
}
