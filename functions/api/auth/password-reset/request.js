import {accountEmailTemplate,createAccountToken,json,normalizeEmail,rateLimit,sameOrigin,sendAccountEmail,sha256,validEmail} from '../../../../server/account-auth.js';

const generic='Si un compte vérifié correspond à cette adresse, un lien de réinitialisation va être envoyé.';

export async function onRequestPost({request,env}){
  if(!sameOrigin(request))return json({error:'Requête refusée'},403);
  if(!env.AX_DB||!env.BREVO_API_KEY||!env.AUTH_EMAIL_FROM)return json({error:'Récupération par e-mail non configurée.'},503);
  let body;try{body=await request.json()}catch{return json({error:'Adresse invalide.'},400)}
  const email=normalizeEmail(body?.email);if(!validEmail(email))return json({error:'Saisis une adresse e-mail valide.'},400);
  try{
    const ip=request.headers.get('CF-Connecting-IP')||'unknown',allowed=await Promise.all([rateLimit(env,`reset:email:${await sha256(email)}`,5),rateLimit(env,`reset:ip:${await sha256(ip)}`,15)]);
    if(allowed.some(value=>!value))return json({ok:true,message:generic});
    const user=await env.AX_DB.prepare('SELECT id,email FROM ax_account_users WHERE email=? AND email_verified_at IS NOT NULL').bind(email).first();
    if(!user)return json({ok:true,message:generic});
    const now=Date.now(),token=await createAccountToken(env,user.id,'reset_password',now+30*60*1000),url=new URL('/?reset='+token,'https://asteriaxverse.pages.dev').href,message='Une demande de changement de mot de passe a été effectuée pour ton compte.';
    await sendAccountEmail(env,{to:user.email,subject:'Réinitialisation du mot de passe Asteriax Verse',text:`${message} Ouvre ce lien pour choisir un nouveau mot de passe : ${url} (valable 30 minutes).`,html:accountEmailTemplate('Réinitialise ton mot de passe',message,'Choisir un nouveau mot de passe',url,'Ce lien expire dans 30 minutes.')});
    return json({ok:true,message:generic});
  }catch{return json({ok:true,message:generic})}
}

