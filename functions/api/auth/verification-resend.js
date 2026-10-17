import {accountEmailTemplate,constantTimeEqual,createAccountToken,json,normalizeEmail,passwordHash,rateLimit,sameOrigin,sendAccountEmail,sha256,validEmail} from '../../../server/account-auth.js';

const fakeSalt='6c8be3e7ab87ec17032f320138bf4e12';

export async function onRequestPost({request,env}){
  if(!sameOrigin(request))return json({error:'Requête refusée'},403);
  if(!env.AX_DB||!env.BREVO_API_KEY||!env.AUTH_EMAIL_FROM)return json({error:'Vérification e-mail non configurée.'},503);
  let body;try{body=await request.json()}catch{return json({error:'Formulaire invalide.'},400)}
  const email=normalizeEmail(body?.email),password=body?.password;if(!validEmail(email)||typeof password!=='string'||password.length>128)return json({error:'Adresse ou mot de passe incorrect.'},400);
  try{
    const ip=request.headers.get('CF-Connecting-IP')||'unknown',allowed=await Promise.all([rateLimit(env,`verify:email:${await sha256(email)}`,5),rateLimit(env,`verify:ip:${await sha256(ip)}`,15)]);
    if(allowed.some(value=>!value))return json({error:'Trop de demandes. Réessaie dans une heure.'},429);
    const user=await env.AX_DB.prepare('SELECT id,email,display_name,password_salt,password_hash,email_verified_at FROM ax_account_users WHERE email=?').bind(email).first();
    const credential=await passwordHash(password,user?.password_salt||fakeSalt);
    if(!user?.password_hash||!constantTimeEqual(credential.hash,user.password_hash))return json({error:'Adresse ou mot de passe incorrect.'},401);
    if(user.email_verified_at)return json({ok:true,message:'Si le compte nécessite une vérification, un e-mail sera envoyé.'});
    const now=Date.now(),token=await createAccountToken(env,user.id,'verify_email',now+24*60*60*1000),url=new URL('/?verify='+token,'https://asteriaxverse.pages.dev').href,message='Confirme ton adresse pour activer ton compte Asteriax Verse.';
    await sendAccountEmail(env,{to:email,subject:'Confirme ton compte Asteriax Verse',text:`${message} Ouvre ce lien : ${url} (valable 24 heures).`,html:accountEmailTemplate('Confirme ton adresse',message,'Vérifier mon adresse',url,'Ce lien expire dans 24 heures.')});
    return json({ok:true,message:'Si le compte nécessite une vérification, un e-mail sera envoyé.'});
  }catch{return json({error:'Envoi temporairement indisponible.'},503)}
}

