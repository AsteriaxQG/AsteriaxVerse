import {issueSession,json,normalizeEmail,normalizeName,passwordHash,rateLimit,randomHex,sameOrigin,sessionCookie,sha256,validEmail,validName,validPassword} from '../../../server/account-auth.js';

export async function onRequestPost({request,env}){
  if(!sameOrigin(request))return json({error:'Requête refusée'},403);
  if(!env.AX_DB)return json({error:'Inscription temporairement indisponible'},503);
  let body;try{body=await request.json()}catch{return json({error:'Formulaire invalide'},400)}
  const email=normalizeEmail(body?.email),name=normalizeName(body?.name),password=body?.password;
  if(!validEmail(email))return json({error:'Saisis une adresse e-mail valide.'},400);
  if(!validName(name))return json({error:'Le nom doit contenir entre 2 et 32 caractères.'},400);
  if(!validPassword(password))return json({error:'Le mot de passe doit contenir entre 12 et 128 caractères.'},400);
  try{
    const ip=request.headers.get('CF-Connecting-IP')||'unknown';
    const allowed=await Promise.all([rateLimit(env,`register:email:${await sha256(email)}`,5),rateLimit(env,`register:ip:${await sha256(ip)}`,15)]);
    if(allowed.some(value=>!value))return json({error:'Trop de tentatives. Réessaie dans une heure.'},429);
    const existing=await env.AX_DB.prepare('SELECT id FROM ax_account_users WHERE email=?').bind(email).first();
    if(existing)return json({error:'Un compte existe déjà avec cette adresse. Connecte-toi.'},409);
    const id=crypto.randomUUID(),credential=await passwordHash(password,randomHex(16)),now=Date.now();
    await env.AX_DB.prepare('INSERT INTO ax_account_users(id,email,display_name,password_salt,password_hash,created_at,last_login_at) VALUES(?,?,?,?,?,?,?)').bind(id,email,name,credential.salt,credential.hash,now,now).run();
    const session=await issueSession(env,id);
    return json({ok:true,authenticated:true,email,name},200,{'Set-Cookie':sessionCookie(session.token)});
  }catch{
    try{const existing=await env.AX_DB.prepare('SELECT id FROM ax_account_users WHERE email=?').bind(email).first();if(existing)return json({error:'Un compte existe déjà avec cette adresse. Connecte-toi.'},409)}catch{}
    return json({error:'Inscription temporairement indisponible.'},503);
  }
}

