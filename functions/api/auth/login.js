import {constantTimeEqual,json,normalizeEmail,passwordHash,rateLimit,sameOrigin,sessionCookie,sha256,issueSession,validEmail} from '../../../server/account-auth.js';

const fakeSalt='8f36c946c7e8d6a8c7b9a56821cfbe43';

export async function onRequestPost({request,env}){
  if(!sameOrigin(request))return json({error:'Requête refusée'},403);
  if(!env.AX_DB)return json({error:'Connexion temporairement indisponible'},503);
  let body;try{body=await request.json()}catch{return json({error:'Adresse ou mot de passe incorrect.'},400)}
  const email=normalizeEmail(body?.email),password=body?.password;
  if(!validEmail(email)||typeof password!=='string'||password.length>128)return json({error:'Adresse ou mot de passe incorrect.'},400);
  try{
    const ip=request.headers.get('CF-Connecting-IP')||'unknown';
    const allowed=await Promise.all([rateLimit(env,`login:email:${await sha256(email)}`,10),rateLimit(env,`login:ip:${await sha256(ip)}`,30)]);
    if(allowed.some(value=>!value))return json({error:'Trop de tentatives. Réessaie dans une heure.'},429);
    const row=await env.AX_DB.prepare('SELECT id,email,display_name,password_salt,password_hash,email_verified_at FROM ax_account_users WHERE email=?').bind(email).first();
    const credential=await passwordHash(password,row?.password_salt||fakeSalt);
    if(!row||!row.password_hash||!constantTimeEqual(credential.hash,row.password_hash))return json({error:'Adresse ou mot de passe incorrect.'},401);
    if(!row.email_verified_at)return json({error:'Adresse e-mail à vérifier.'},403);
    const now=Date.now();
    await env.AX_DB.prepare('UPDATE ax_account_users SET last_login_at=? WHERE id=?').bind(now,row.id).run();
    const session=await issueSession(env,row.id);
    return json({ok:true,authenticated:true,email:row.email,name:row.display_name},200,{'Set-Cookie':sessionCookie(session.token)});
  }catch{return json({error:'Connexion temporairement indisponible.'},503)}
}

