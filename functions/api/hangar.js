import {cleanIds,json,sameOrigin,sessionFor} from '../../server/account-auth.js';

export async function onRequestGet({request,env}){
  if(!env.AX_DB)return json({error:'Synchronisation non configurée'},503);
  try{const user=await sessionFor(request,env);if(!user)return json({error:'Connexion requise'},401);const row=await env.AX_DB.prepare('SELECT owned_json,wishlist_json,updated_at FROM ax_account_hangars WHERE user_id=?').bind(user.id).first();return json({owned:JSON.parse(row?.owned_json||'[]'),wishlist:JSON.parse(row?.wishlist_json||'[]'),updatedAt:row?.updated_at||null})}catch{return json({error:'Synchronisation indisponible'},503)}
}
export async function onRequestPut({request,env}){
  if(!sameOrigin(request))return json({error:'Requête refusée'},403);
  if(!env.AX_DB)return json({error:'Synchronisation non configurée'},503);
  let body;try{body=await request.json()}catch{return json({error:'Données invalides'},400)}
  const owned=cleanIds(body?.owned),wishlist=cleanIds(body?.wishlist);if(!owned||!wishlist)return json({error:'Liste de vaisseaux invalide'},400);
  const ownedSet=new Set(owned),cleanWishlist=wishlist.filter(id=>!ownedSet.has(id)),now=Date.now();
  try{const user=await sessionFor(request,env);if(!user)return json({error:'Connexion requise'},401);await env.AX_DB.prepare('INSERT INTO ax_account_hangars(user_id,owned_json,wishlist_json,updated_at) VALUES(?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET owned_json=excluded.owned_json,wishlist_json=excluded.wishlist_json,updated_at=excluded.updated_at').bind(user.id,JSON.stringify(owned),JSON.stringify(cleanWishlist),now).run();return json({ok:true,updatedAt:now})}catch{return json({error:'Synchronisation indisponible'},503)}
}

