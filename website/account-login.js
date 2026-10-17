(()=>{
  'use strict';
  const hangar=window.AsteriaxHangar;
  const panel=document.querySelector('#hangar .ax-account');
  if(!hangar||!panel)return;
  const english=()=>window.AsteriaxI18n?.isEnglish?.()===true;
  const copy=en=>en?{
    title:'Sync your hangar',guest:'Your ships and wish list are saved on this device. Sign in by email to sync them across your devices.',signed:'Your hangar and wish list are saved to your account.',email:'Email address',send:'Send a sign-in code',code:'6-digit code',verify:'Sign in and sync',resend:'Send another code',logout:'Sign out',sent:'If the address is valid, a sign-in code is on its way. Check your inbox and spam folder.',busy:'Please wait…',local:'Saved on this device',synced:'Account sync active',badCode:'That code is invalid or expired. Request a new one.',setup:'Email sign-in is not configured yet. You can keep using your local hangar.',network:'The service is temporarily unavailable. Your local hangar is safe.',emailError:'Enter a valid email address.',emailUsed:'Email address',verified:'Signed in. Your local hangar has been merged and synced.'
  }:{
    title:'Synchroniser ton Hangar',guest:'Tes vaisseaux et ta liste d’envie sont enregistrés sur cet appareil. Connecte-toi par e-mail pour les retrouver sur tes autres appareils.',signed:'Ton Hangar et ta liste d’envie sont enregistrés sur ton compte.',email:'Adresse e-mail',send:'Recevoir un code de connexion',code:'Code à 6 chiffres',verify:'Connexion et synchronisation',resend:'Renvoyer un code',logout:'Déconnexion',sent:'Si l’adresse est valide, un code arrive par e-mail. Pense à vérifier les courriers indésirables.',busy:'Patiente un instant…',local:'Enregistré sur cet appareil',synced:'Synchronisation du compte active',badCode:'Ce code est invalide ou expiré. Demande-en un nouveau.',setup:'La connexion e-mail n’est pas encore configurée. Ton Hangar local reste disponible.',network:'Le service est momentanément indisponible. Ton Hangar local est en sécurité.',emailError:'Saisis une adresse e-mail valide.',emailUsed:'Adresse e-mail',verified:'Connecté. Ton Hangar local a été fusionné et synchronisé.'
  };
  panel.classList.add('ax-account-auth');
  const copyArea=panel.querySelector('.ax-account-copy');
  const title=panel.querySelector('#axAccountTitle');
  const status=panel.querySelector('#axAccountStatus');
  const ui=document.createElement('div');ui.className='ax-account-login';ui.dataset.i18nSkip='';
  ui.innerHTML='<form class="ax-account-email-form" novalidate><label class="ax-account-email-label" for="axAccountEmail"></label><div class="ax-account-form-row"><input id="axAccountEmail" name="email" type="email" autocomplete="email" maxlength="254" required/><button class="ax-account-button primary" type="submit"></button></div><p class="ax-account-feedback" role="status" aria-live="polite"></p></form><form class="ax-account-code-form" novalidate hidden><label class="ax-account-email-label" for="axAccountCode"></label><div class="ax-account-form-row"><input id="axAccountCode" name="code" type="text" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]{6}" maxlength="6" required/><button class="ax-account-button primary" type="submit"></button></div><div class="ax-account-secondary"><button class="ax-account-text-button" type="button" data-resend></button><button class="ax-account-text-button" type="button" data-back></button></div><p class="ax-account-feedback" role="status" aria-live="polite"></p></form><div class="ax-account-signed" hidden><span class="ax-account-email"></span><button class="ax-account-button" type="button" data-logout></button></div>';
  panel.append(ui);
  const emailForm=ui.querySelector('.ax-account-email-form'),codeForm=ui.querySelector('.ax-account-code-form'),signed=ui.querySelector('.ax-account-signed');
  const emailInput=ui.querySelector('#axAccountEmail'),codeInput=ui.querySelector('#axAccountCode');
  const emailFeedback=emailForm.querySelector('.ax-account-feedback'),codeFeedback=codeForm.querySelector('.ax-account-feedback');
  let user=null,syncing=false,pendingSync=false,syncTimer=0,emailPending='';
  function paint(message=''){
    const en=english(),t=copy(en);
    if(title)title.textContent=t.title;
    if(status)status.textContent=user?t.signed:t.guest;
    emailForm.hidden=Boolean(user)||Boolean(emailPending);
    codeForm.hidden=Boolean(user)||!emailPending;
    signed.hidden=!user;
    emailForm.querySelector('label').textContent=t.email;
    emailForm.querySelector('button[type="submit"]').textContent=t.send;
    emailInput.setAttribute('aria-label',t.email);emailInput.placeholder=t.email;
    codeForm.querySelector('label').textContent=t.code;
    codeForm.querySelector('button[type="submit"]').textContent=t.verify;
    codeInput.setAttribute('aria-label',t.code);codeInput.placeholder=t.code;
    ui.querySelector('[data-resend]').textContent=t.resend;
    ui.querySelector('[data-back]').textContent=en?'Change address':'Changer d’adresse';
    ui.querySelector('[data-logout]').textContent=t.logout;
    if(user)ui.querySelector('.ax-account-email').textContent=`${t.synced} · ${user.email}`;
    if(message){const target=emailPending?codeFeedback:emailFeedback;target.textContent=message;}
  }
  async function api(url,options={}){
    const response=await fetch(url,{...options,headers:{'Content-Type':'application/json',...(options.headers||{})},cache:'no-store',credentials:'same-origin'});
    let data={};try{data=await response.json()}catch{}
    if(!response.ok){const error=new Error(data.error||'Request failed');error.status=response.status;throw error}
    return data;
  }
  const snapshot=()=>hangar.read();
  async function pushHangar(){
    if(!user)return;
    if(syncing){pendingSync=true;return}
    syncing=true;
    try{do{pendingSync=false;await api('/api/hangar',{method:'PUT',body:JSON.stringify(snapshot())})}while(pendingSync)}
    catch{status.textContent=copy(english()).network}
    finally{syncing=false}
  }
  async function restoreAndMerge(){
    const remote=await api('/api/hangar');
    const local=snapshot(),owned=[...new Set([...remote.owned,...local.owned].map(String))],ownedSet=new Set(owned);
    const wishlist=[...new Set([...remote.wishlist,...local.wishlist].map(String))].filter(id=>!ownedSet.has(id));
    hangar.replace({owned,wishlist});
    await pushHangar();
  }
  async function loadSession(){
    try{const data=await api('/api/auth/session');user=data.authenticated?{email:data.email}:null;paint();if(user)await restoreAndMerge()}
    catch{paint()}
  }
  async function sendCode(){
    const t=copy(english()),email=emailInput.value.trim();
    if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)){paint(t.emailError);emailInput.focus();return}
    const button=emailForm.querySelector('button[type="submit"]');button.disabled=true;button.textContent=t.busy;emailFeedback.textContent='';
    try{await api('/api/auth/request',{method:'POST',body:JSON.stringify({email})});emailPending=email.toLowerCase();codeFeedback.textContent=t.sent;paint();codeInput.focus()}
    catch(error){paint(error.status===503?t.setup:t.network)}
    finally{button.disabled=false;button.textContent=copy(english()).send}
  }
  async function verifyCode(){
    const t=copy(english()),code=codeInput.value.trim(),button=codeForm.querySelector('button[type="submit"]');
    if(!/^\d{6}$/.test(code)){paint(t.badCode);codeInput.focus();return}
    button.disabled=true;button.textContent=t.busy;codeFeedback.textContent='';
    try{const data=await api('/api/auth/verify',{method:'POST',body:JSON.stringify({email:emailPending,code})});user={email:data.email};emailPending='';paint(t.verified);await restoreAndMerge();paint(t.verified)}
    catch(error){paint(error.status===503?t.setup:error.status===401?t.badCode:t.network)}
    finally{button.disabled=false;button.textContent=copy(english()).verify}
  }
  emailForm.addEventListener('submit',event=>{event.preventDefault();void sendCode()});
  codeForm.addEventListener('submit',event=>{event.preventDefault();void verifyCode()});
  ui.querySelector('[data-resend]').addEventListener('click',()=>void sendCode());
  ui.querySelector('[data-back]').addEventListener('click',()=>{emailPending='';codeInput.value='';paint()});
  ui.querySelector('[data-logout]').addEventListener('click',async event=>{event.currentTarget.disabled=true;try{await api('/api/auth/session',{method:'DELETE'})}catch{}user=null;emailPending='';paint();event.currentTarget.disabled=false});
  document.addEventListener('asteriax:hangar-edit',()=>{if(!user)return;clearTimeout(syncTimer);syncTimer=setTimeout(()=>void pushHangar(),450)});
  document.addEventListener('asteriax:language-change',()=>paint());
  paint();void loadSession();
})();

