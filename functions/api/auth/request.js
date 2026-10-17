import {codeHash,json,normalizeEmail,randomHex,sha256,sameOrigin,validEmail} from '../../../server/account-auth.js';

export async function onRequestPost({request,env}){
  if(!sameOrigin(request))return json({error:'Requête refusée'},403);
  const mailProvider=env.BREVO_API_KEY?'brevo':env.RESEND_API_KEY?'resend':'';
  if(!env.AX_DB||!mailProvider||!env.AUTH_EMAIL_FROM||!env.ACCOUNT_AUTH_SECRET)return json({error:'Connexion e-mail non configurée'},503);
  let body;try{body=await request.json()}catch{return json({error:'Adresse invalide'},400)}
  const email=normalizeEmail(body?.email);if(!validEmail(email))return json({error:'Saisis une adresse e-mail valide'},400);
  const ip=request.headers.get('CF-Connecting-IP')||'unknown',now=Date.now(),hour=Math.floor(now/3600000)*3600000;
  try{
    await Promise.all([
      env.AX_DB.prepare('DELETE FROM ax_account_login_codes WHERE expires_at<?').bind(now).run(),
      env.AX_DB.prepare('DELETE FROM ax_account_rate_limits WHERE window_start<?').bind(hour-24*60*60*1000).run()
    ]);
    const [emailRate,ipRate]=await Promise.all([
      env.AX_DB.prepare('INSERT INTO ax_account_rate_limits(bucket,window_start,hits) VALUES(?,?,1) ON CONFLICT(bucket,window_start) DO UPDATE SET hits=hits+1 RETURNING hits').bind(`email:${await sha256(email)}`,hour).first(),
      env.AX_DB.prepare('INSERT INTO ax_account_rate_limits(bucket,window_start,hits) VALUES(?,?,1) ON CONFLICT(bucket,window_start) DO UPDATE SET hits=hits+1 RETURNING hits').bind(`ip:${await sha256(ip)}`,hour).first()
    ]);
    if(Number(emailRate?.hits)>5||Number(ipRate?.hits)>20)return json({ok:true,message:'Si cette adresse est valide, un code de connexion va lui être envoyé.'});
    const limit=Math.floor(0x100000000/1000000)*1000000;let entropy=0;do{entropy=crypto.getRandomValues(new Uint32Array(1))[0]}while(entropy>=limit);
    const code=String(entropy%1000000).padStart(6,'0'),expires=now+10*60*1000;
    await env.AX_DB.prepare('INSERT INTO ax_account_login_codes(email,code_hash,created_at,expires_at,attempts) VALUES(?,?,?,?,0) ON CONFLICT(email) DO UPDATE SET code_hash=excluded.code_hash,created_at=excluded.created_at,expires_at=excluded.expires_at,attempts=0').bind(email,await codeHash(email,code,env.ACCOUNT_AUTH_SECRET),now,expires).run();
    const text=`Ton code de connexion est ${code}. Il expire dans 10 minutes. Si tu n'es pas à l'origine de cette demande, ignore ce message.`;
    const html=`<div style="font-family:Arial,sans-serif;background:#071018;color:#e8f7ff;padding:28px;border-radius:16px"><p style="color:#48dcff;letter-spacing:.16em;font-size:12px;font-weight:bold">ASTERIAX VERSE</p><h1 style="font-size:22px">Ton code de connexion</h1><p>Entre ce code sur le site pour retrouver ton Hangar et ta liste d’envie :</p><p style="font-size:34px;letter-spacing:.28em;font-weight:bold;color:#72e5ff">${code}</p><p>Il expire dans 10 minutes. Si tu n’es pas à l’origine de cette demande, ignore ce message.</p></div>`;
    const resend=mailProvider==='resend';
    const result=await fetch(resend?'https://api.resend.com/emails':'https://api.brevo.com/v3/smtp/email',{method:'POST',headers:resend?{Authorization:`Bearer ${env.RESEND_API_KEY}`,'Content-Type':'application/json'}:{'api-key':env.BREVO_API_KEY,'Content-Type':'application/json'},body:JSON.stringify(resend?{from:env.AUTH_EMAIL_FROM,to:[email],subject:'Ton code de connexion à Asteriax Verse',text,html}:{sender:{email:env.AUTH_EMAIL_FROM,name:'Asteriax Verse'},to:[{email}],subject:'Ton code de connexion à Asteriax Verse',textContent:text,htmlContent:html})});
    if(!result.ok){await env.AX_DB.prepare('DELETE FROM ax_account_login_codes WHERE email=?').bind(email).run();return json({error:'Le service d’e-mail n’a pas accepté l’envoi. Vérifie sa configuration puis réessaie.'},502)}
    return json({ok:true,message:'Si cette adresse est valide, un code de connexion va lui être envoyé.'});
  }catch{return json({error:'Connexion temporairement indisponible'},503)}
}

