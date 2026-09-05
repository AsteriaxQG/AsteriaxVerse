// Server-only helpers. Never bundle this file into website/.
export const ORIGIN='https://asteriaxverse.pages.dev';
export const CALLBACK=ORIGIN+'/api/twitch/callback';
export const CHANNEL='asteriaxttv';
export const SESSION_COOKIE='__Host-ax_session';
export const STATE_COOKIE='__Host-ax_oauth';
export const now=()=>Math.floor(Date.now()/1000);
export const ready=env=>Boolean(env.AX_DB&&env.TWITCH_CLIENT_ID&&env.TWITCH_CLIENT_SECRET&&env.AX_TOKEN_KEY);
export function json(data,status=200){return Response.json(data,{status,headers:{'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer'}})}
export function cookie(name,value,age){return `${name}=${value}; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=${age}`}
export function readCookie(request,name){return (request.headers.get('Cookie')||'').split(';').map(s=>s.trim()).find(s=>s.startsWith(name+'='))?.slice(name.length+1)||''}
export function random(){return [...crypto.getRandomValues(new Uint8Array(32))].map(n=>n.toString(16).padStart(2,'0')).join('')}
export async function hash(value){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value)))].map(n=>n.toString(16).padStart(2,'0')).join('')}
export async function allow(request,env,bucket,limit,windowSeconds){
  const ip=request.headers.get('CF-Connecting-IP')||'unknown',id=await hash(env.AX_TOKEN_KEY+':'+ip),time=now(),expires=time+windowSeconds;
  const row=await env.AX_DB.prepare("INSERT INTO ax_rate(bucket,key,count,expires) VALUES(?,?,1,?) ON CONFLICT(bucket,key) DO UPDATE SET count=CASE WHEN ax_rate.expires<=? THEN 1 ELSE ax_rate.count+1 END,expires=CASE WHEN ax_rate.expires<=? THEN excluded.expires ELSE ax_rate.expires END RETURNING count").bind(bucket,id,expires,time,time).first();
  return Number(row?.count)<=limit;
}
async function key(env){if(!/^[a-f0-9]{64}$/i.test(env.AX_TOKEN_KEY||''))throw Error('Invalid encryption key');return crypto.subtle.importKey('raw',Uint8Array.from(env.AX_TOKEN_KEY.match(/../g),n=>parseInt(n,16)),{name:'AES-GCM'},false,['encrypt','decrypt'])}
export async function seal(value,env){const iv=crypto.getRandomValues(new Uint8Array(12));const data=new Uint8Array(await crypto.subtle.encrypt({name:'AES-GCM',iv},await key(env),new TextEncoder().encode(value)));return btoa(String.fromCharCode(...iv,...data))}
export async function unseal(value,env){const data=Uint8Array.from(atob(value),c=>c.charCodeAt(0));return new TextDecoder().decode(await crypto.subtle.decrypt({name:'AES-GCM',iv:data.slice(0,12)},await key(env),data.slice(12)))}
export async function twitchFetch(url,options={}){return fetch(url,{...options,signal:AbortSignal.timeout(8000)})}
export async function tokenRequest(env,extra){const r=await twitchFetch('https://id.twitch.tv/oauth2/token',{method:'POST',body:new URLSearchParams({client_id:env.TWITCH_CLIENT_ID,client_secret:env.TWITCH_CLIENT_SECRET,...extra})});if(!r.ok)throw Error('Twitch token unavailable');const data=await r.json();if(!data.access_token||!(data.expires_in>0))throw Error('Invalid token response');return data}
export async function validate(token,env){const r=await twitchFetch('https://id.twitch.tv/oauth2/validate',{headers:{Authorization:'OAuth '+token}});if(r.status===401)return null;if(!r.ok)throw Error('Twitch validation unavailable');const v=await r.json();return v.client_id===env.TWITCH_CLIENT_ID&&v.expires_in>0?v:null}
export async function session(request,env){
  const raw=readCookie(request,SESSION_COOKIE);if(!/^[a-f0-9]{64}$/.test(raw))return null;
  const id=await hash(raw);const s=await env.AX_DB.prepare('SELECT * FROM ax_sessions WHERE hash=? AND expires>?').bind(id,now()).first();if(!s)return null;
  const token=await unseal(s.token,env),v=await validate(token,env);
  if(!v||v.user_id!==s.user_id){await env.AX_DB.prepare('DELETE FROM ax_sessions WHERE hash=?').bind(id).run();return null}
  return{id:s.user_id,login:s.login,sessionHash:id,token};
}
export function sameOrigin(request){return new URL(request.url).origin===ORIGIN&&request.headers.get('Origin')===ORIGIN}
export async function body(request){
  if(!/^application\/json(?:;|$)/i.test(request.headers.get('Content-Type')||''))throw Error('Invalid content type');
  const reader=request.body?.getReader();if(!reader)throw Error('Missing body');let size=0;const chunks=[];
  for(;;){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>65536){await reader.cancel();throw Error('Payload too large')}chunks.push(value)}
  const data=new Uint8Array(size);let offset=0;for(const chunk of chunks){data.set(chunk,offset);offset+=chunk.length}return JSON.parse(new TextDecoder().decode(data));
}
export async function appToken(env){
  const cached=await env.AX_DB.prepare('SELECT * FROM ax_app_tokens WHERE id=? AND expires>?').bind(env.TWITCH_CLIENT_ID,now()+120).first();if(cached)return unseal(cached.token,env);
  const t=await tokenRequest(env,{grant_type:'client_credentials'});
  await env.AX_DB.prepare('INSERT INTO ax_app_tokens(id,token,expires) VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET token=excluded.token,expires=excluded.expires').bind(env.TWITCH_CLIENT_ID,await seal(t.access_token,env),now()+t.expires_in).run();return t.access_token;
}
