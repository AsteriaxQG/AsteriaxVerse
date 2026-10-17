import {accountEmailTemplate,createAccountToken,json,normalizeEmail,normalizeName,passwordHash,rateLimit,randomHex,sameOrigin,sendAccountEmail,sha256,validEmail,validName,validPassword} from '../../../server/account-auth.js';

export async function onRequestPost({request,env}){
  if(!sameOrigin(request))return json({error:'Requête refusée'},403);
  if(!env.AX_DB||!env.BREVO_API_KEY||!env.AUTH_EMAIL_FROM)return json({error:'Inscription temporairement indisponible : vérification e-mail non configurée.'},503);
  let body;try{body=await request.json()}catch{return json({error:'Formulaire invalide'},400)}
  const email=normalizeEmail(body?.email),name=normalizeName(body?.name),password=body?.password;
  if(!validEmail(email))return json({error:'Saisis une adresse e-mail valide.'},400);
  if(!validName(name))return json({error:'Le nom doit contenir entre 2 et 32 caractères.'},400);
  if(!validPassword(password))return json({error:'Le mot de passe doit contenir entre 12 et 128 caractères.'},400);
  try{
    const ip=request.headers.get('CF-Connecting-IP')||'unknown';
    const allowed=await Promise.all([rateLimit(env,`register:email:${await sha256(email)}`,5),rateLimit(env,`register:ip:${await sha256(ip)}`,15)]);
    if(allowed.some(value=>!value))return json({error:'Trop de tentatives. Réessaie dans une heure.'},429);
    const existing=await env.AX_DB.prepare('SELECT id,email_verified_at FROM ax_account_users WHERE email=?').bind(email).first();
    if(existing?.email_verified_at)return json({error:'Un compte existe déjà avec cette adresse. Connecte-toi.'},409);
    const id=existing?.id||crypto.randomUUID(),credential=await passwordHash(password,randomHex(16)),now=Date.now();
    const user=await env.AX_DB.prepare("INSERT INTO ax_account_users(id,email,display_name,password_salt,password_hash,created_at,last_login_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(email) DO UPDATE SET display_name=excluded.display_name,password_salt=excluded.password_salt,password_hash=excluded.password_hash,last_login_at=excluded.last_login_at WHERE ax_account_users.email_verified_at IS NULL RETURNING id").bind(id,email,name,credential.salt,credential.hash,now,now).first();
    if(!user)return json({error:'Un compte existe déjà avec cette adresse. Connecte-toi.'},409);
    const token=await createAccountToken(env,user.id,'verify_email',now+24*60*60*1000),url=new URL('/?verify='+token,'https://asteriaxverse.pages.dev').href;
    const message='Confirme ton adresse pour activer ton compte et synchroniser ton Hangar.';
    await sendAccountEmail(env,{to:email,subject:'Confirme ton compte Asteriax Verse',text:`${message} Ouvre ce lien : ${url} (valable 24 heures).`,html:accountEmailTemplate('Confirme ton adresse',message,'Vérifier mon adresse',url,'Ce lien expire dans 24 heures.')});
    return json({ok:true,verificationRequired:true,email});
  }catch{return json({error:'Inscription ou envoi de la vérification temporairement indisponible. Réessaie avec la même adresse.'},503)}
}

