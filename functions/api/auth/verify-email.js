import {issueSession,json,sameOrigin,sessionCookie,sha256} from '../../../server/account-auth.js';

export async function onRequestPost({request,env}){
  if(!sameOrigin(request))return json({error:'Requête refusée'},403);
  if(!env.AX_DB)return json({error:'Vérification temporairement indisponible.'},503);
  let body;try{body=await request.json()}catch{return json({error:'Lien invalide ou expiré.'},400)}
  const token=String(body?.token||'');if(!/^[a-f0-9]{64}$/.test(token))return json({error:'Lien invalide ou expiré.'},400);
  try{
    const tokenHash=await sha256(token),now=Date.now();
    const consumed=await env.AX_DB.prepare("DELETE FROM ax_account_email_tokens WHERE token_hash=? AND purpose='verify_email' AND expires_at>? RETURNING user_id").bind(tokenHash,now).first();
    if(!consumed)return json({error:'Ce lien de vérification est invalide ou expiré.'},400);
    await env.AX_DB.prepare('UPDATE ax_account_users SET email_verified_at=? WHERE id=? AND email_verified_at IS NULL').bind(now,consumed.user_id).run();
    const user=await env.AX_DB.prepare('SELECT id,email,display_name FROM ax_account_users WHERE id=?').bind(consumed.user_id).first();
    if(!user)return json({error:'Compte introuvable.'},404);
    const session=await issueSession(env,user.id);
    return json({ok:true,authenticated:true,email:user.email,name:user.display_name},200,{'Set-Cookie':sessionCookie(session.token)});
  }catch{return json({error:'Vérification temporairement indisponible.'},503)}
}

