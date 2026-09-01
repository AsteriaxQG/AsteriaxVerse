const API='https://api.star-citizen.wiki/api/shipmatrix/vehicles';
const RSI='https://robertsspaceindustries.com';

function normalize(v){
  const media=Array.isArray(v.media)?v.media:[];
  const image=media.map(m=>m?.source_url||m?.images?.slideshow_wide||m?.images?.hub_large||m?.images?.post).find(Boolean)||'';
  const manufacturer=v.manufacturer?.name||v.manufacturer_name||'';
  const status=String(v.production_status||'').toLowerCase();
  return {
    rsi_id:v.id,
    name:v.name||'',
    manufacturer,
    status:status||'unknown',
    status_note:v.production_note||'',
    focus:v.focus||'',
    type:v.type||'',
    size:v.size||'',
    scu:v.cargocapacity??null,
    crew_min:v.min_crew??null,
    crew_max:v.max_crew??null,
    length:v.length??null,
    beam:v.beam??null,
    height:v.height??null,
    msrp:v.msrp??null,
    description:v.description||'',
    image,
    rsi_url:v.url?`${RSI}${String(v.url).startsWith('/')?v.url:'/'+v.url}`:'',
    updated:v.time_modified||''
  };
}

export async function onRequestGet(context){
  const cache=caches.default;
  const key=new Request(new URL('/api/ships?catalog=v1',context.request.url).toString());
  const cached=await cache.match(key);
  if(cached)return cached;
  try{
    const url=`${API}?page%5Bsize%5D=200&sort=name`;
    const r=await fetch(url,{headers:{Accept:'application/json','User-Agent':'AsteriaxVerse/1.0'}});
    if(!r.ok)throw new Error(`Ship Matrix API ${r.status}`);
    const json=await r.json();
    let data=Array.isArray(json.data)?json.data:[];
    const pages=Number(json.meta?.last_page||1);
    if(pages>1){
      const rest=await Promise.all(Array.from({length:pages-1},(_,i)=>fetch(`${API}?page%5Bsize%5D=200&page%5Bnumber%5D=${i+2}&sort=name`,{headers:{Accept:'application/json','User-Agent':'AsteriaxVerse/1.0'}}).then(x=>x.ok?x.json():{data:[]})));
      rest.forEach(x=>{if(Array.isArray(x.data))data.push(...x.data)});
    }
    const items=data.map(normalize).filter(x=>x.name);
    const response=new Response(JSON.stringify({ok:true,source:'RSI Ship Matrix via Star Citizen Wiki API',updatedAt:new Date().toISOString(),items}),{headers:{'content-type':'application/json; charset=utf-8','cache-control':'public, max-age=300, s-maxage=21600, stale-while-revalidate=86400','access-control-allow-origin':'*'}});
    context.waitUntil(cache.put(key,response.clone()));
    return response;
  }catch(error){
    return new Response(JSON.stringify({ok:false,error:String(error?.message||error),items:[]}),{status:502,headers:{'content-type':'application/json; charset=utf-8','cache-control':'no-store'}});
  }
}
