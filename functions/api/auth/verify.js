import {codeHash,constantTimeEqual,issueSession,json,normalizeEmail,sameOrigin,sessionCookie,validEmail} from '../../../server/account-auth.js';

export async function onRequestPost({request,env}){
  if(!sameOrigin(request))return json({error:'Requête refusée'},403);
  if(!env.AX_DB||!env.ACCOUNT_AUTH_SECRET)return json({error:'Connexion e-mail non configurée'},503);
  let body;try{body=await request.json()}catch{return json({error:'Code invalide'},400)}
  const email=normalizeEmail(body?.email),code=String(body?.code||'').trim();if(!validEmail(email)||!/^\d{6}$/.test(code))return json({error:'Adresse ou code invalide'},400);
  try{
    const row=await env.AX_DB.prepare('SELECT code_hash,expires_at,attempts FROM ax_account_login_codes WHERE email=?').bind(email).first();
    if(!row||Number(row.expires_at)<=Date.now()||Number(row.attempts)>=5){await env.AX_DB.prepare('DELETE FROM ax_account_login_codes WHERE email=?').bind(email).run();return json({error:'Code invalide ou expiré. Demande-en un nouveau.'},401)}
    const expected=await codeHash(email,code,env.ACCOUNT_AUTH_SECRET);
    if(!constantTimeEqual(expected,row.code_hash)){await env.AX_DB.prepare('UPDATE ax_account_login_codes SET attempts=attempts+1 WHERE email=?').bind(email).run();return json({error:'Code invalide ou expiré. Demande-en un nouveau.'},401)}
    const consumed=await env.AX_DB.prepare('DELETE FROM ax_account_login_codes WHERE email=? AND code_hash=? AND expires_at>? AND attempts<5 RETURNING email').bind(email,expected,Date.now()).first();
    if(!consumed)return json({error:'Code invalide ou expiré. Demande-en un nouveau.'},401);
    const now=Date.now(),user=await env.AX_DB.prepare('INSERT INTO ax_account_users(id,email,created_at,last_login_at) VALUES(?,?,?,?) ON CONFLICT(email) DO UPDATE SET last_login_at=excluded.last_login_at RETURNING id,email').bind(crypto.randomUUID(),email,now,now).first();
    const session=await issueSession(env,user.id);
    return json({ok:true,authenticated:true,email:user.email},{headers:{'Set-Cookie':sessionCookie(session.token)}});
  }catch{return json({error:'Connexion temporairement indisponible'},503)}
}

