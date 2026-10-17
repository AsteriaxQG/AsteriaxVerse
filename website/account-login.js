(()=>{
  'use strict';
  const hangar=window.AsteriaxHangar,panel=document.querySelector('#hangar .ax-account');
  if(!hangar||!panel)return;
  const english=()=>window.AsteriaxI18n?.isEnglish?.()===true;
  const copy=en=>en?{
    title:'Your Asteriax account',guest:'Create an account or sign in to sync your hangar and wish list across devices.',signed:'Your hangar and wish list are synced to your account.',register:'Create account',login:'Sign in',name:'Display name',email:'Email address',password:'Password',passwordHint:'12 characters minimum.',create:'Create my account',connect:'Sign in and sync',logout:'Sign out',busy:'Please wait…',network:'The service is temporarily unavailable. Your local hangar is safe.',emailError:'Enter a valid email address.',nameError:'Use a display name between 2 and 32 characters.',passwordError:'Choose a password between 12 and 128 characters.',accountExists:'An account already uses this address. Sign in instead.',credentials:'Email or password is incorrect.',rate:'Too many attempts. Try again in an hour.',registered:'Account created. Your local hangar has been merged and synced.',connected:'Signed in. Your local hangar has been merged and synced.'
  }:{
    title:'Ton compte Asteriax',guest:'Crée un compte ou connecte-toi pour synchroniser ton Hangar et ta Liste d’envie entre tes appareils.',signed:'Ton Hangar et ta Liste d’envie sont synchronisés avec ton compte.',register:'Créer un compte',login:'Se connecter',name:'Nom affiché',email:'Adresse e-mail',password:'Mot de passe',passwordHint:'12 caractères minimum.',create:'Créer mon compte',connect:'Connexion et synchronisation',logout:'Déconnexion',busy:'Patiente un instant…',network:'Le service est momentanément indisponible. Ton Hangar local est en sécurité.',emailError:'Saisis une adresse e-mail valide.',nameError:'Choisis un nom affiché de 2 à 32 caractères.',passwordError:'Le mot de passe doit contenir entre 12 et 128 caractères.',accountExists:'Un compte utilise déjà cette adresse. Connecte-toi plutôt.',credentials:'Adresse e-mail ou mot de passe incorrect.',rate:'Trop de tentatives. Réessaie dans une heure.',registered:'Compte créé. Ton Hangar local a été fusionné et synchronisé.',connected:'Connecté. Ton Hangar local a été fusionné et synchronisé.'
  };
  panel.classList.add('ax-account-auth');
  const title=panel.querySelector('#axAccountTitle'),status=panel.querySelector('#axAccountStatus');
  const ui=document.createElement('div');ui.className='ax-account-login';ui.dataset.i18nSkip='';
  ui.innerHTML='<div class="ax-account-modes" role="tablist"><button type="button" data-mode="register" role="tab"></button><button type="button" data-mode="login" role="tab"></button></div><form class="ax-account-form" novalidate><div class="ax-account-name-field"><label class="ax-account-email-label" for="axAccountName"></label><input id="axAccountName" name="name" type="text" autocomplete="nickname" maxlength="32"/></div><label class="ax-account-email-label" for="axAccountEmail"></label><input class="ax-account-input" id="axAccountEmail" name="email" type="email" autocomplete="email" maxlength="254" required/><label class="ax-account-email-label" for="axAccountPassword"></label><input class="ax-account-input" id="axAccountPassword" name="password" type="password" autocomplete="new-password" minlength="12" maxlength="128" required/><small class="ax-account-password-hint"></small><button class="ax-account-button primary ax-account-submit" type="submit"></button><p class="ax-account-feedback" role="status" aria-live="polite"></p></form><div class="ax-account-signed" hidden><span class="ax-account-email"></span><button class="ax-account-button" type="button" data-logout></button></div>';
  panel.append(ui);
  const form=ui.querySelector('.ax-account-form'),nameField=ui.querySelector('.ax-account-name-field'),nameInput=ui.querySelector('#axAccountName'),emailInput=ui.querySelector('#axAccountEmail'),passwordInput=ui.querySelector('#axAccountPassword'),feedback=ui.querySelector('.ax-account-feedback'),signed=ui.querySelector('.ax-account-signed');
  let user=null,mode='register',syncing=false,pendingSync=false,syncTimer=0;
  function setMode(value){mode=value==='login'?'login':'register';paint();feedback.textContent='';passwordInput.value='';passwordInput.focus()}
  function paint(message=''){
    const en=english(),t=copy(en);
    if(title)title.textContent=t.title;
    if(status)status.textContent=user?t.signed:t.guest;
    ui.querySelectorAll('[data-mode]').forEach(button=>{const active=button.dataset.mode===mode;button.textContent=button.dataset.mode==='register'?t.register:t.login;button.classList.toggle('active',active);button.setAttribute('aria-selected',String(active));button.tabIndex=active?0:-1});
    nameField.hidden=mode!=='register';
    nameField.querySelector('label').textContent=t.name;nameInput.placeholder=t.name;
    form.querySelector('label[for="axAccountEmail"]').textContent=t.email;emailInput.placeholder=t.email;
    form.querySelector('label[for="axAccountPassword"]').textContent=t.password;passwordInput.placeholder=t.password;
    passwordInput.autocomplete=mode==='register'?'new-password':'current-password';
    ui.querySelector('.ax-account-password-hint').textContent=mode==='register'?t.passwordHint:'';
    ui.querySelector('.ax-account-submit').textContent=mode==='register'?t.create:t.connect;
    form.hidden=Boolean(user);signed.hidden=!user;
    ui.querySelector('[data-logout]').textContent=t.logout;
    if(user)ui.querySelector('.ax-account-email').textContent=`${user.name||user.email} · ${user.email}`;
    if(message)feedback.textContent=message;
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
    const remote=await api('/api/hangar'),local=snapshot();
    const owned=[...new Set([...remote.owned,...local.owned].map(String))],ownedSet=new Set(owned);
    const wishlist=[...new Set([...remote.wishlist,...local.wishlist].map(String))].filter(id=>!ownedSet.has(id));
    hangar.replace({owned,wishlist});await pushHangar();
  }
  async function loadSession(){
    try{const data=await api('/api/auth/session');user=data.authenticated?{email:data.email,name:data.name}:null;paint();if(user)await restoreAndMerge()}
    catch{paint()}
  }
  function errorMessage(error){const t=copy(english());if(error.status===409)return t.accountExists;if(error.status===401)return t.credentials;if(error.status===429)return t.rate;if(error.status===400)return mode==='register'?(emailInput.validity.typeMismatch?t.emailError:passwordInput.value.length<12?t.passwordError:t.nameError):t.credentials;return t.network}
  async function submit(event){
    event.preventDefault();const t=copy(english()),email=emailInput.value.trim(),password=passwordInput.value;
    if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)){feedback.textContent=t.emailError;emailInput.focus();return}
    if(mode==='register'&&Array.from(nameInput.value.trim()).length<2){feedback.textContent=t.nameError;nameInput.focus();return}
    if(mode==='register'&&(Array.from(password).length<12||Array.from(password).length>128)){feedback.textContent=t.passwordError;passwordInput.focus();return}
    if(!password||password.length>128){feedback.textContent=t.credentials;passwordInput.focus();return}
    const button=ui.querySelector('.ax-account-submit');button.disabled=true;button.textContent=t.busy;feedback.textContent='';
    try{
      const data=await api(mode==='register'?'/api/auth/register':'/api/auth/login',{method:'POST',body:JSON.stringify({name:nameInput.value,email,password})});
      user={email:data.email,name:data.name};passwordInput.value='';paint(mode==='register'?t.registered:t.connected);
      try{await restoreAndMerge()}catch{status.textContent=t.network}
      paint(mode==='register'?t.registered:t.connected);
    }catch(error){feedback.textContent=errorMessage(error)}
    finally{button.disabled=false;button.textContent=copy(english())[mode==='register'?'create':'connect']}
  }
  ui.querySelectorAll('[data-mode]').forEach(button=>button.addEventListener('click',()=>setMode(button.dataset.mode)));
  form.addEventListener('submit',submit);
  ui.querySelector('[data-logout]').addEventListener('click',async event=>{event.currentTarget.disabled=true;try{await api('/api/auth/session',{method:'DELETE'})}catch{}user=null;passwordInput.value='';paint();event.currentTarget.disabled=false});
  document.addEventListener('asteriax:hangar-edit',()=>{if(!user)return;clearTimeout(syncTimer);syncTimer=setTimeout(()=>void pushHangar(),450)});
  document.addEventListener('asteriax:language-change',()=>paint());
  paint();void loadSession();
})();

