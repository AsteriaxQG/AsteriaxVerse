import {SITE,releases,embed,digest} from './changelog.js';
const json=(data,status=200)=>Response.json(data,{status,headers:{'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
export async function publish(request,env,source,send=(...args)=>fetch(...args)) {
  if(request.method!=='POST')return json({error:'Method not allowed'},405);
  if(new URL(request.url).origin!==SITE)return json({error:'Production only'},403);
  if(!env.CHANGELOG_PUBLISH_TOKEN || env.CHANGELOG_PUBLISH_TOKEN.length<32)return json({error:'Publisher not configured'},503);
  const supplied=request.headers.get('Authorization')||'';
  if(supplied.length>1024 || await digest(supplied)!==await digest('Bearer '+env.CHANGELOG_PUBLISH_TOKEN))return json({error:'Unauthorized'},401);
  if(!env.AX_DB || !env.DISCORD_CHANGELOG_WEBHOOK)return json({error:'Missing changelog binding or webhook'},503);
  let url,v,payload,hash;
  try {
    url=new URL(env.DISCORD_CHANGELOG_WEBHOOK);
    if(url.protocol!=='https:' || url.hostname!=='discord.com' || url.port || !/^\/api\/webhooks\/\d+\/[A-Za-z0-9_-]+$/.test(url.pathname))throw Error();
    url.search='?wait=true';v=releases(source)[0];payload=embed(v);hash=await digest(JSON.stringify(v));
  }catch{return json({error:'Invalid changelog or webhook configuration'},422)}
  // Authenticated, read-only check. Never expose the webhook URL/token or Discord response body.
  if(request.headers.get('X-Changelog-Action')==='diagnose'){
    try{
      const check=await send(url.toString(),{redirect:'error',signal:AbortSignal.timeout(12000)});
      const result=await check.json().catch(()=>({}));
      return json({webhookReachable:check.ok,discordStatus:check.status,discordCode:Number.isInteger(result.code)?result.code:null,webhookType:Number.isInteger(result.type)?result.type:null});
    }catch(error){return json({error:'Discord network request failed',kind:['TypeError','TimeoutError','AbortError'].includes(error.name)?error.name:'Error',reason:/invocation|this reference/i.test(error.message)?'fetch binding':/timeout/i.test(error.message)?'timeout':/redirect/i.test(error.message)?'redirect':/resolve|dns/i.test(error.message)?'dns':'runtime'},502)}
  }
  try {
    // Claim before the external side effect. Never automatically reclaim an ambiguous send.
    const claim=await env.AX_DB.prepare("INSERT INTO ax_changelog_publications(version,status,content_hash,created_at) VALUES(?,'sending',?,?) ON CONFLICT(version) DO NOTHING RETURNING version").bind(v.version,hash,new Date().toISOString()).first();
    if(!claim){
      const row=await env.AX_DB.prepare('SELECT status,content_hash FROM ax_changelog_publications WHERE version=?').bind(v.version).first();
      return json({version:v.version,status:row?.status||'reserved',alreadyPublished:row?.status==='published',contentChanged:row?.content_hash!==hash},row?.status==='published'?200:409);
    }
    let message;
    try {
      const response=await send(url.toString(),{method:'POST',redirect:'error',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal:AbortSignal.timeout(12000)});
      if(!response.ok){const details=await response.json().catch(()=>({}));throw Object.assign(new Error('Discord rejected request'),{discordStatus:response.status,discordCode:Number.isInteger(details.code)?details.code:null})}
      message=await response.json();if(!message.id)throw Error();
    }catch(error){
      await env.AX_DB.prepare("UPDATE ax_changelog_publications SET status='uncertain' WHERE version=?").bind(v.version).run();
      return json({version:v.version,status:'uncertain',discordStatus:error.discordStatus||null,discordCode:error.discordCode||null,error:'Check Discord before any manual retry; automatic resend is blocked'},502);
    }
    await env.AX_DB.prepare("UPDATE ax_changelog_publications SET status='published',published_at=?,discord_message_id=? WHERE version=?").bind(new Date().toISOString(),message.id,v.version).run();
    return json({version:v.version,status:'published'});
  }catch{return json({error:'Publication storage unavailable; check D1 before retrying'},503)}
}