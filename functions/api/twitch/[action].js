import {ORIGIN,CHANNEL,json,appToken,twitchFetch} from '../../../server/twitch.js';

export async function onRequest(ctx){
  const {request,env}=ctx,action=ctx.params.action;
  if(action!=='live'||request.method!=='GET')return json({error:'La connexion Twitch a été supprimée'},410);
  if(!env.AX_DB||!env.TWITCH_CLIENT_ID||!env.TWITCH_CLIENT_SECRET||!env.AX_TOKEN_KEY)return json({configured:false,error:'Statut Twitch indisponible'},503);
  if(new URL(request.url).origin!==ORIGIN)return json({error:'Production origin required'},403);
  try{
    const cache=caches.default,key=new Request(ORIGIN+'/api/twitch/live?cache=v2'),cached=await cache.match(key);
    if(cached)return cached;
    let token=await appToken(env);
    const get=()=>twitchFetch('https://api.twitch.tv/helix/streams?user_login='+CHANNEL,{headers:{Authorization:'Bearer '+token,'Client-Id':env.TWITCH_CLIENT_ID}});
    let response=await get();
    if(response.status===401){
      await env.AX_DB.prepare('DELETE FROM ax_app_tokens WHERE id=?').bind(env.TWITCH_CLIENT_ID).run();
      token=await appToken(env);
      response=await get();
    }
    if(!response.ok)throw Error('Stream lookup unavailable');
    const data=await response.json();
    if(!Array.isArray(data.data))throw Error('Invalid stream response');
    const stream=data.data.find(entry=>entry.user_login?.toLowerCase()===CHANNEL&&entry.type==='live');
    const result=json({configured:true,live:!!stream,channel:CHANNEL,title:stream?.title||'',checkedAt:new Date().toISOString()});
    result.headers.set('Cache-Control','public, max-age=30, s-maxage=60');
    ctx.waitUntil(cache.put(key,result.clone()));
    return result;
  }catch{
    return json({configured:true,error:'Twitch temporairement indisponible',live:null},503);
  }
}

