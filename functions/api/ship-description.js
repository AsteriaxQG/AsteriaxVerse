const TRANSLATE_ENDPOINT='https://translate.googleapis.com/translate_a/single';
function json(body,status=200,cache='public, max-age=86400, s-maxage=604800, stale-while-revalidate=2592000'){return new Response(JSON.stringify(body),{status,headers:{'content-type':'application/json; charset=utf-8','cache-control':cache,'access-control-allow-origin':'*'}})}
export async function onRequestGet(context){
 const requestUrl=new URL(context.request.url),text=requestUrl.searchParams.get('text')?.trim()||'';
 if(!text)return json({ok:false,error:'Texte manquant'},400,'no-store');
 if(text.length>5000)return json({ok:false,error:'Texte trop long'},413,'no-store');
 const cacheKey=new Request(requestUrl.toString()),cached=await caches.default.match(cacheKey);if(cached)return cached;
 try{
  let translated='';
  try{
   const endpoint=new URL(TRANSLATE_ENDPOINT);endpoint.searchParams.set('client','gtx');endpoint.searchParams.set('sl','en');endpoint.searchParams.set('tl','fr');endpoint.searchParams.set('dt','t');endpoint.searchParams.set('q',text);
   const response=await fetch(endpoint,{headers:{Accept:'application/json','User-Agent':'AsteriaxVerse/1.0'}});if(response.ok){const payload=await response.json();translated=Array.isArray(payload?.[0])?payload[0].map(part=>Array.isArray(part)?part[0]:'').filter(Boolean).join(' ').trim():''}
  }catch{}
  if(!translated){
   const fallback=new URL('https://api.mymemory.translated.net/get');fallback.searchParams.set('q',text);fallback.searchParams.set('langpair','en|fr');
   const response=await fetch(fallback,{headers:{Accept:'application/json','User-Agent':'AsteriaxVerse/1.0'}});if(response.ok){const payload=await response.json();translated=String(payload?.responseData?.translatedText||'').trim()}
  }
  if(!translated)throw new Error('Réponse de traduction vide');
  const result=json({ok:true,text:translated});context.waitUntil(caches.default.put(cacheKey,result.clone()));return result;
 }catch(error){return json({ok:false,error:String(error?.message||error)},502,'no-store')}
}

