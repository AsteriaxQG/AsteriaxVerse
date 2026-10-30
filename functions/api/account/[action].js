const enc = new TextEncoder();
const json = (body, status = 200, headers = {}) => new Response(JSON.stringify(body), {status, headers: {'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', ...headers}});
const bytes = n => { const b = new Uint8Array(n); crypto.getRandomValues(b); return b; };
const hex = b => Array.from(b, x => x.toString(16).padStart(2, '0')).join('');
const digest = async s => hex(new Uint8Array(await crypto.subtle.digest('SHA-256', enc.encode(s))));
const passwordHash = async (password, salt) => { const key = await crypto.subtle.importKey('raw', enc.encode(password), 'PBKDF2', false, ['deriveBits']); return hex(new Uint8Array(await crypto.subtle.deriveBits({name:'PBKDF2',salt:Uint8Array.from(salt.match(/../g).map(x=>parseInt(x,16))),iterations:100000,hash:'SHA-256'},key,256))); };
const same = (a,b) => { if (a.length !== b.length) return false; let d=0; for(let i=0;i<a.length;i++) d|=a.charCodeAt(i)^b.charCodeAt(i); return d===0; };
const cookie = (token, maxAge) => `ax_hangar_session=${token}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${maxAge}`;
const getToken = request => /(?:^|;\s*)ax_hangar_session=([a-f0-9]{64})(?:;|$)/.exec(request.headers.get('cookie')||'')?.[1];
async function schema(db) {
  await db.prepare('CREATE TABLE IF NOT EXISTS ax_hangar_users (id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE COLLATE NOCASE, display_name TEXT NOT NULL, password_salt TEXT NOT NULL, password_hash TEXT NOT NULL, created_at INTEGER NOT NULL)').run();
  await db.prepare('CREATE TABLE IF NOT EXISTS ax_hangar_sessions (token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, expires_at INTEGER NOT NULL)').run();
  await db.prepare('CREATE TABLE IF NOT EXISTS ax_hangar_items (user_id TEXT NOT NULL, ship_id TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN (\'owned\',\'wishlist\')), updated_at INTEGER NOT NULL, PRIMARY KEY(user_id,ship_id))').run();
  await db.prepare('CREATE TABLE IF NOT EXISTS ax_hangar_insurance (user_id TEXT NOT NULL, ship_id TEXT NOT NULL, term TEXT NOT NULL CHECK(term IN (\'6m\',\'24m\',\'120m\',\'lti\')), updated_at INTEGER NOT NULL, PRIMARY KEY(user_id,ship_id))').run();
  await db.prepare('CREATE TABLE IF NOT EXISTS ax_hangar_attempts (bucket TEXT PRIMARY KEY, hits INTEGER NOT NULL, reset_at INTEGER NOT NULL)').run();
}
async function body(request) { if(Number(request.headers.get('content-length')||0)>10000) throw Error('too_large'); const raw=await request.text(); if(raw.length>10000) throw Error('too_large'); return JSON.parse(raw||'{}'); }
async function userFor(db, request) { const token=getToken(request); if(!token) return null; return db.prepare('SELECT u.id,u.email,u.display_name FROM ax_hangar_sessions s JOIN ax_hangar_users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>?').bind(await digest(token),Date.now()).first(); }
async function issue(db, user, responseBody) { const token=hex(bytes(32)); await db.prepare('INSERT INTO ax_hangar_sessions(token_hash,user_id,expires_at) VALUES(?,?,?)').bind(await digest(token),user.id,Date.now()+30*86400000).run(); return json(responseBody,200,{'set-cookie':cookie(token,30*86400)}); }
async function list(db, userId) { const rows=await db.prepare('SELECT ship_id,status FROM ax_hangar_items WHERE user_id=?').bind(userId).all(); const terms=await db.prepare('SELECT ship_id,term FROM ax_hangar_insurance WHERE user_id=?').bind(userId).all(); return {owned:rows.results.filter(x=>x.status==='owned').map(x=>x.ship_id),wishlist:rows.results.filter(x=>x.status==='wishlist').map(x=>x.ship_id),insurance:Object.fromEntries(terms.results.map(x=>[x.ship_id,x.term]))}; }
async function rate(db, request, key) { const ip=request.headers.get('CF-Connecting-IP')||'unknown'; const bucket=await digest(`${key}:${ip}`); const now=Date.now(), row=await db.prepare('SELECT hits,reset_at FROM ax_hangar_attempts WHERE bucket=?').bind(bucket).first(); if(row&&row.reset_at>now&&row.hits>=10) return false; await db.prepare('INSERT INTO ax_hangar_attempts(bucket,hits,reset_at) VALUES(?,?,?) ON CONFLICT(bucket) DO UPDATE SET hits=CASE WHEN reset_at<? THEN 1 ELSE hits+1 END,reset_at=CASE WHEN reset_at<? THEN excluded.reset_at ELSE reset_at END').bind(bucket,1,now+900000,now,now).run(); return true; }
export async function onRequest(context) {
  const {request,env,params}=context, action=params.action, method=request.method;
  if(!env.AX_DB) return json({error:'Base de données indisponible'},503);
  if(method==='POST'&&request.headers.get('origin')!==new URL(request.url).origin) return json({error:'Origine refusée'},403);
  try {
    const db=env.AX_DB; await schema(db);
    if(action==='session'&&method==='GET') { const user=await userFor(db,request); return json(user?{user,hangar:await list(db,user.id)}:{user:null}); }
    if(action==='register'&&method==='POST') {
      if(!await rate(db,request,'register')) return json({error:'Trop de tentatives. Réessaie dans 15 minutes.'},429);
      const data=await body(request), email=String(data.email||'').trim().toLowerCase(), name=String(data.name||'').trim(), password=String(data.password||'');
      if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)||email.length>254||name.length<2||name.length>60||Array.from(password).length<12||password.length>128) return json({error:'Indique un nom, un e-mail valide et un mot de passe de 12 caractères minimum.'},400);
      if(await db.prepare('SELECT id FROM ax_hangar_users WHERE email=?').bind(email).first()) return json({error:'Cette adresse possède déjà un compte.'},409);
      const id=crypto.randomUUID(),salt=hex(bytes(16)),hash=await passwordHash(password,salt);
      await db.prepare('INSERT INTO ax_hangar_users(id,email,display_name,password_salt,password_hash,created_at) VALUES(?,?,?,?,?,?)').bind(id,email,name,salt,hash,Date.now()).run();
      return issue(db,{id},{user:{id,email,display_name:name},hangar:{owned:[],wishlist:[]},newAccount:true});
    }
    if(action==='login'&&method==='POST') {
      if(!await rate(db,request,'login')) return json({error:'Trop de tentatives. Réessaie dans 15 minutes.'},429);
      const data=await body(request),email=String(data.email||'').trim().toLowerCase(),password=String(data.password||'');
      if(email.length>254||password.length>128) return json({error:'Identifiants invalides.'},401);
      const user=await db.prepare('SELECT * FROM ax_hangar_users WHERE email=?').bind(email).first();
      const hash=await passwordHash(password,user?.password_salt||'00000000000000000000000000000000');
      if(!user||!same(hash,user.password_hash)) return json({error:'Identifiants invalides.'},401);
      return issue(db,user,{user:{id:user.id,email:user.email,display_name:user.display_name},hangar:await list(db,user.id)});
    }
    if(action==='logout'&&method==='POST') { const token=getToken(request); if(token) await db.prepare('DELETE FROM ax_hangar_sessions WHERE token_hash=?').bind(await digest(token)).run(); return json({ok:true},200,{'set-cookie':cookie('',0)}); }
    if(action==='hangar'&&method==='POST') {
      const user=await userFor(db,request); if(!user) return json({error:'Connexion nécessaire'},401);
      const data=await body(request);
      if(data.import===true) { const owned=Array.isArray(data.owned)?data.owned:[],wishlist=Array.isArray(data.wishlist)?data.wishlist:[],insurance=data.insurance&&typeof data.insurance==='object'?data.insurance:{}; if(owned.length+wishlist.length>1000||Object.keys(insurance).length>1000) return json({error:'Liste trop grande'},400); for(const [status,ids] of [['owned',owned],['wishlist',wishlist]]) for(const id of ids) { if(typeof id!=='string'||id.length>120||!id) return json({error:'Vaisseau invalide'},400); await db.prepare('INSERT OR REPLACE INTO ax_hangar_items(user_id,ship_id,status,updated_at) VALUES(?,?,?,?)').bind(user.id,id,status,Date.now()).run(); } for(const [id,term] of Object.entries(insurance)){if(!id||id.length>120||!['6m','24m','120m','lti'].includes(term))return json({error:'Assurance invalide'},400);await db.prepare('INSERT OR REPLACE INTO ax_hangar_insurance(user_id,ship_id,term,updated_at) VALUES(?,?,?,?)').bind(user.id,id,term,Date.now()).run()} return json({hangar:await list(db,user.id)}); }
      if(data.insurance!==undefined){const id=data.id,term=data.insurance;if(typeof id!=='string'||!id||id.length>120||!['','6m','24m','120m','lti'].includes(term))return json({error:'Assurance invalide'},400);if(!term)await db.prepare('DELETE FROM ax_hangar_insurance WHERE user_id=? AND ship_id=?').bind(user.id,id).run();else await db.prepare('INSERT OR REPLACE INTO ax_hangar_insurance(user_id,ship_id,term,updated_at) VALUES(?,?,?,?)').bind(user.id,id,term,Date.now()).run();return json({ok:true})}
      const id=data.id,status=data.status; if(typeof id!=='string'||!id||id.length>120||!['owned','wishlist','none'].includes(status)) return json({error:'Modification invalide'},400);
      if(status==='none') await db.prepare('DELETE FROM ax_hangar_items WHERE user_id=? AND ship_id=?').bind(user.id,id).run();
      else await db.prepare('INSERT OR REPLACE INTO ax_hangar_items(user_id,ship_id,status,updated_at) VALUES(?,?,?,?)').bind(user.id,id,status,Date.now()).run();
      return json({ok:true});
    }
    return json({error:'Route introuvable'},404);
  } catch(e) { console.error('Hangar account error',e); return json({error:'Service momentanément indisponible'},500); }
}
