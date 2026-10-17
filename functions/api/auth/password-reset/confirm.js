import {json,passwordHash,rateLimit,sameOrigin,sha256,validPassword} from '../../../../server/account-auth.js';

export async function onRequestPost({request,env}){
  if(!sameOrigin(request))return json({error:'Requête refusée'},403);
  if(!env.AX_DB)return json({error:'Réinitialisation temporairement indisponible.'},503);
  let body;try{body=await request.json()}catch{return json({error:'Formulaire invalide.'},400)}
  const token=String(body?.token||''),password=body?.password;
  if(!/^[a-f0-9]{64}$/.test(token)||!validPassword(password))return json({error:'Lien invalide ou mot de passe trop court.'},400);
  try{
    const ip=request.headers.get('CF-Connecting-IP')||'unknown';if(!await rateLimit(env,`reset-confirm:ip:${await sha256(ip)}`,15))return json({error:'Trop de tentatives. Réessaie dans une heure.'},429);
    const tokenHash=await sha256(token),now=Date.now(),consumed=await env.AX_DB.prepare("DELETE FROM ax_account_email_tokens WHERE token_hash=? AND purpose='reset_password' AND expires_at>? RETURNING user_id").bind(tokenHash,now).first();
    if(!consumed)return json({error:'Ce lien est invalide ou expiré. Demande-en un nouveau.'},400);
    const credential=await passwordHash(password);
    await env.AX_DB.prepare('UPDATE ax_account_users SET password_salt=?,password_hash=? WHERE id=?').bind(credential.salt,credential.hash,consumed.user_id).run();
    await env.AX_DB.prepare('DELETE FROM ax_account_sessions WHERE user_id=?').bind(consumed.user_id).run();
    await env.AX_DB.prepare("DELETE FROM ax_account_email_tokens WHERE user_id=? AND purpose='reset_password'").bind(consumed.user_id).run();
    return json({ok:true});
  }catch{return json({error:'Réinitialisation temporairement indisponible.'},503)}
}

