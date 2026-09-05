import {ORIGIN,CALLBACK,CHANNEL,SESSION_COOKIE,STATE_COOKIE,now,ready,json,cookie,readCookie,random,hash,seal,tokenRequest,validate,session,sameOrigin,appToken,twitchFetch,allow} from '../../../server/twitch.js';
function redirect(location,cookies=[]){const headers=new Headers({'Location':location,'Cache-Control':'no-store','Referrer-Policy':'no-referrer'});for(const c of cookies)headers.append('Set-Cookie',c);return new Response(null,{status:303,headers})}
export async function onRequest(ctx){
  const {request,env}=ctx,action=ctx.params.action;
  if(!ready(env))return json({configured:false,error:'Connexion Twitch en préparation'},503);
  if(new URL(request.url).origin!==ORIGIN)return json({error:'Production origin required'},403);
  try{
    if(action==='login'&&request.method==='GET'){
      if(!await allow(request,env,'login',20,3600))return json({error:'Trop de tentatives, réessaie plus tard'},429);
      const state=random();await env.AX_DB.batch([
        env.AX_DB.prepare('DELETE FROM ax_oauth_states WHERE expires<?').bind(now()),
        env.AX_DB.prepare('DELETE FROM ax_sessions WHERE expires<?').bind(now()),
        env.AX_DB.prepare('INSERT INTO ax_oauth_states(hash,expires) VALUES(?,?)').bind(await hash(state),now()+600)
      ]);
      const url=new URL('https://id.twitch.tv/oauth2/authorize');url.search=new URLSearchParams({client_id:env.TWITCH_CLIENT_ID,redirect_uri:CALLBACK,response_type:'code',scope:'',state,force_verify:'true'}).toString();
      return redirect(url.toString(),[cookie(STATE_COOKIE,state,600)]);
    }
    if(action==='callback'&&request.method==='GET'){
      const url=new URL(request.url),state=url.searchParams.get('state'),expected=readCookie(request,STATE_COOKIE);
      const failed=()=>redirect(ORIGIN+'/?twitch=error#hangar',[cookie(STATE_COOKIE,'',0)]);
      if(!state||!expected||state!==expected||!/^[a-f0-9]{64}$/.test(state))return failed();
      const used=await env.AX_DB.prepare('DELETE FROM ax_oauth_states WHERE hash=? AND expires>? RETURNING hash').bind(await hash(state),now()).first();
      if(!used||url.searchParams.has('error')||!url.searchParams.get('code'))return failed();
      const t=await tokenRequest(env,{grant_type:'authorization_code',code:url.searchParams.get('code'),redirect_uri:CALLBACK});
      const v=await validate(t.access_token,env);if(!v?.user_id||!v.login)return failed();
      const raw=random(),age=Math.min(7*86400,t.expires_in,v.expires_in),old=readCookie(request,SESSION_COOKIE);
      await env.AX_DB.batch([
        env.AX_DB.prepare('DELETE FROM ax_sessions WHERE hash=?').bind(await hash(old)),
        env.AX_DB.prepare('INSERT INTO ax_sessions(hash,user_id,login,token,expires) VALUES(?,?,?,?,?)').bind(await hash(raw),v.user_id,v.login,await seal(t.access_token,env),now()+age)
      ]);
      return redirect(ORIGIN+'/?twitch=connected#hangar',[cookie(STATE_COOKIE,'',0),cookie(SESSION_COOKIE,raw,age)]);
    }
    if(action==='session'&&request.method==='GET'){
      const s=await session(request,env);return json({configured:true,user:s?{id:s.id,login:s.login}:null});
    }
    if(action==='logout'&&request.method==='POST'){
      if(!sameOrigin(request))return json({error:'Origin rejected'},403);
      const id=await hash(readCookie(request,SESSION_COOKIE));await env.AX_DB.prepare('DELETE FROM ax_sessions WHERE hash=?').bind(id).run();
      const r=json({ok:true});r.headers.set('Set-Cookie',cookie(SESSION_COOKIE,'',0));return r;
    }
    if(action==='live'&&request.method==='GET'){
      const cache=caches.default,key=new Request(ORIGIN+'/api/twitch/live?cache=v1'),cached=await cache.match(key);if(cached)return cached;
      let token=await appToken(env);
      const get=()=>twitchFetch('https://api.twitch.tv/helix/streams?user_login='+CHANNEL,{headers:{Authorization:'Bearer '+token,'Client-Id':env.TWITCH_CLIENT_ID}});
      let r=await get();if(r.status===401){await env.AX_DB.prepare('DELETE FROM ax_app_tokens WHERE id=?').bind(env.TWITCH_CLIENT_ID).run();token=await appToken(env);r=await get()}
      if(!r.ok)throw Error('Stream lookup unavailable');const data=await r.json();if(!Array.isArray(data.data))throw Error('Invalid stream response');
      const stream=data.data.find(s=>s.user_login?.toLowerCase()===CHANNEL&&s.type==='live');
      const response=json({configured:true,live:!!stream,channel:CHANNEL,title:stream?.title||'',checkedAt:new Date().toISOString()});response.headers.set('Cache-Control','public, max-age=30, s-maxage=60');
      ctx.waitUntil(cache.put(key,response.clone()));return response;
    }
    return json({error:'Not found'},404);
  }catch{return json({configured:true,error:'Twitch temporairement indisponible',live:null},503)}
}
