import {expiredSessionCookie,json,sameOrigin,sessionFor,sha256} from '../../../server/account-auth.js';

export async function onRequestGet({request,env}){
  if(!env.AX_DB)return json({error:'Connexion e-mail non configurée'},503);
  try{const user=await sessionFor(request,env);return json(user?{authenticated:true,email:user.email}:{authenticated:false})}catch{return json({error:'Connexion temporairement indisponible'},503)}
}
export async function onRequestDelete({request,env}){
  if(!sameOrigin(request))return json({error:'Requête refusée'},403);
  try{const user=await sessionFor(request,env);if(user){const token=(request.headers.get('Cookie')||'').split(';').map(x=>x.trim()).find(x=>x.startsWith('__Host-asteriax_session='))?.slice('__Host-asteriax_session='.length);if(token)await env.AX_DB.prepare('DELETE FROM ax_account_sessions WHERE token_hash=?').bind(await sha256(token)).run()}}catch{return json({error:'Déconnexion temporairement indisponible'},503,{'Set-Cookie':expiredSessionCookie})}
  return json({ok:true,authenticated:false},{headers:{'Set-Cookie':expiredSessionCookie}});
}

