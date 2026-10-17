const MANIFEST='https://install.robertsspaceindustries.com/rel/2/latest.yml';
const DOWNLOAD='https://robertsspaceindustries.com/en/download';
const headers={'content-type':'application/json; charset=utf-8','cache-control':'public, max-age=30, s-maxage=300'};

export function parseLauncherManifest(body){
  const version=String(body).match(/^version:\s*["']?(\d+\.\d+\.\d+)["']?\s*$/m)?.[1];
  if(!version)throw new Error('Invalid stable launcher manifest');
  const rawDate=String(body).match(/^releaseDate:\s*["']?([^"'\r\n]+)["']?\s*$/m)?.[1]?.trim();
  const publishedAt=rawDate&&Number.isFinite(Date.parse(rawDate))?new Date(rawDate).toISOString():'';
  return{version,publishedAt,source:MANIFEST,url:DOWNLOAD};
}

export async function onRequestGet(context){
  const cache=caches.default;
  const key=new Request(new URL('/api/launcher?cache=v1',context.request.url));
  const lastKey=new Request(new URL('/api/launcher-last-good?cache=v1',context.request.url));
  const cached=await cache.match(key);if(cached)return cached;
  try{
    const response=await fetch(MANIFEST,{headers:{Accept:'text/yaml,text/plain,*/*'},signal:AbortSignal.timeout(8000),cache:'no-store'});
    if(!response.ok)throw new Error('Launcher manifest unavailable');
    const data={ok:true,...parseLauncherManifest(await response.text()),checkedAt:new Date().toISOString(),stale:false};
    const result=new Response(JSON.stringify(data),{headers});
    context.waitUntil(Promise.all([cache.put(key,result.clone()),cache.put(lastKey,new Response(JSON.stringify(data),{headers:{...headers,'cache-control':'public, max-age=86400'}}))]));
    return result;
  }catch{
    const last=await cache.match(lastKey);
    if(last){const data=await last.json();return new Response(JSON.stringify({...data,stale:true}),{headers:{...headers,'cache-control':'public, max-age=30, s-maxage=60'}})}
    return new Response(JSON.stringify({ok:false,version:'',url:DOWNLOAD,source:MANIFEST}),{status:503,headers:{...headers,'cache-control':'no-store'}});
  }
}
