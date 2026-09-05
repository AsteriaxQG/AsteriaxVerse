import {ready,json,session,sameOrigin,body,now,allow} from '../../server/twitch.js';
export function validOperations(ops){return Array.isArray(ops)&&ops.length>0&&ops.length<=20&&ops.every(o=>o&&typeof o.shipId==='string'&&/^[a-zA-Z0-9:_-]{1,160}$/.test(o.shipId)&&['owned','wishlist','none'].includes(o.status)&&typeof o.mutationId==='string'&&/^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/.test(o.mutationId))}
export async function onRequest({request,env}){
  if(!ready(env))return json({configured:false,error:'Synchronisation en préparation'},503);
  if(!['GET','POST'].includes(request.method))return json({error:'Method not allowed'},405);
  if(request.method==='POST'&&!sameOrigin(request))return json({error:'Origin rejected'},403);
  try{
    if(!await allow(request,env,'hangar',request.method==='POST'?240:600,60))return json({error:'Trop de requêtes, réessaie plus tard'},429);
    const user=await session(request,env);if(!user)return json({error:'Connexion requise'},401);
    if(request.method==='GET'){
      const {results}=await env.AX_DB.prepare('SELECT ship_id,status FROM ax_hangar WHERE user_id=?').bind(user.id).all();
      return json({userId:user.id,owned:results.filter(r=>r.status==='owned').map(r=>r.ship_id),wishlist:results.filter(r=>r.status==='wishlist').map(r=>r.ship_id)});
    }
    let data;try{data=await body(request)}catch{return json({error:'Invalid JSON body'},400)}
    if(data?.userId!==user.id)return json({error:'Compte changé : recharge la page'},409);
    if(!validOperations(data.operations)||!['set','import'].includes(data.mode))return json({error:'Invalid operations'},400);
    const statements=[];
    for(const o of data.operations){
      // Persistent mutation IDs prevent retries from overwriting a newer edit on another device.
      const conflict=data.mode==='import'?'DO NOTHING':'DO UPDATE SET status=excluded.status,updated=excluded.updated';
      statements.push(env.AX_DB.prepare(`INSERT INTO ax_hangar(user_id,ship_id,status,updated) SELECT ?,?,?,? WHERE NOT EXISTS(SELECT 1 FROM ax_mutations WHERE user_id=? AND id=?) ON CONFLICT(user_id,ship_id) ${conflict}`).bind(user.id,o.shipId,o.status,now(),user.id,o.mutationId));
      statements.push(env.AX_DB.prepare('INSERT OR IGNORE INTO ax_mutations(user_id,id,created) VALUES(?,?,?)').bind(user.id,o.mutationId,now()));
    }
    statements.push(env.AX_DB.prepare('DELETE FROM ax_mutations WHERE created<?').bind(now()-2592000));
    await env.AX_DB.batch(statements);return json({ok:true,userId:user.id});
  }catch{return json({error:'Synchronisation indisponible, modifications conservées sur cet appareil'},503)}
}
