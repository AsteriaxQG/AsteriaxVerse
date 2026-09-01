const STATUS_URL='https://status.robertsspaceindustries.com/';
const PTU_FAQ='https://support.robertsspaceindustries.com/hc/en-us/articles/115013195927-Public-Test-Universe-PTU-FAQ';
const LOANER_MATRIX='https://support.robertsspaceindustries.com/hc/en-us/articles/360003093114-Loaner-Ship-Matrix';
const PATCH_FORUM='https://robertsspaceindustries.com/spectrum/community/SC/forum/190048?page=1&sort=newest';

function decode(s=''){return String(s).replace(/&nbsp;|&#160;/gi,' ').replace(/&amp;/gi,'&').replace(/&quot;/gi,'"').replace(/&#39;|&apos;/gi,"'").replace(/&lt;/gi,'<').replace(/&gt;/gi,'>')}
function text(html=''){return decode(html.replace(/<script[\s\S]*?<\/script>/gi,' ').replace(/<style[\s\S]*?<\/style>/gi,' ').replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim())}
async function fetchText(url){const r=await fetch(url,{headers:{Accept:'text/html,application/xhtml+xml','Accept-Language':'en-US,en;q=0.9','User-Agent':'AsteriaxVerse/2.0'}});if(!r.ok)throw new Error(`${url} ${r.status}`);return r.text()}
function serviceStatus(body,name){const re=new RegExp(`${name.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}\\s+(Operational|Degraded Performance|Partial Outage|Major Outage|Maintenance|Degraded|Offline)`,`i`);const m=body.match(re);return m?m[1]:'Unknown'}
function frStatus(v=''){const s=String(v).toLowerCase();if(s.includes('operational'))return'Opérationnel';if(s.includes('degraded'))return'Dégradé';if(s.includes('partial'))return'Incident partiel';if(s.includes('major'))return'Incident majeur';if(s.includes('maintenance'))return'Maintenance';if(s.includes('offline'))return'Hors ligne';if(s.includes('online'))return'En ligne';return v||'Inconnu'}
function buildMatches(body,label){const re=new RegExp(`\\b(\\d+(?:\\.\\d+){1,3}-${label}\\.\\d+)\\b`,'ig');return [...body.matchAll(re)].map(m=>m[1])}
function versionOnly(build=''){return String(build).match(/^\d+(?:\.\d+){1,3}/)?.[0]||''}

export async function onRequestGet(context){
  const cache=caches.default;
  const cacheKey=new Request(new URL('/api/status?cache=v2',context.request.url).toString());
  const cached=await cache.match(cacheKey);if(cached)return cached;
  const settled=await Promise.allSettled([fetchText(STATUS_URL),fetchText(PTU_FAQ),fetchText(LOANER_MATRIX),fetchText(PATCH_FORUM)]);
  const statusBody=settled[0].status==='fulfilled'?text(settled[0].value):'';
  const ptuBody=settled[1].status==='fulfilled'?text(settled[1].value):'';
  const loanerBody=settled[2].status==='fulfilled'?text(settled[2].value):'';
  const patchBody=settled[3].status==='fulfilled'?text(settled[3].value):'';

  const matrixBuild=loanerBody.match(/Last Updated:[^|]{0,80}\|\s*(\d+(?:\.\d+){1,3}-live\.\d+)/i)?.[1]||'';
  const statusLiveBuild=buildMatches(statusBody,'live')[0]||'';
  const liveBuild=matrixBuild||statusLiveBuild;
  const ptuHeader=ptuBody.match(/PTU STATUS:\s*([^|]{1,40})\|\s*LIVE STATUS:\s*([\d.]+)/i);
  const ptuBuilds=[...buildMatches(patchBody,'ptu'),...buildMatches(ptuBody,'ptu')];
  const eptuBuilds=[...buildMatches(patchBody,'eptu'),...buildMatches(ptuBody,'eptu')];
  const ptuState=(ptuHeader?.[1]||'').trim()|| (ptuBuilds.length?'Online':'Unknown');
  const eptuState=eptuBuilds.length?'Online':'Non publié';

  const platform=serviceStatus(statusBody,'Platform');
  const pu=serviceStatus(statusBody,'Persistent Universe');
  const arena=serviceStatus(statusBody,'Arena Commander');
  const noIssues=/No issues detected/i.test(statusBody);
  let overall=noIssues&&/Operational/i.test(platform)&&/Operational/i.test(pu)?'Operational':'Unknown';
  if(/Major Outage/i.test(statusBody))overall='Major Outage';
  else if(/Partial Outage/i.test(statusBody))overall='Partial Outage';
  else if(/Degraded Performance|\bDegraded\b/i.test(statusBody)&&!noIssues)overall='Degraded';
  else if(/Maintenance/i.test(statusBody)&&!noIssues)overall='Maintenance';

  const payload={
    ok:Boolean(statusBody||ptuBody||loanerBody),
    updatedAt:new Date().toISOString(),
    live:{version:versionOnly(liveBuild)||(ptuHeader?.[2]||''),build:liveBuild,status:frStatus(overall)},
    ptu:{version:versionOnly(ptuBuilds[0]||''),build:ptuBuilds[0]||'',status:frStatus(ptuState)},
    eptu:{version:versionOnly(eptuBuilds[0]||''),build:eptuBuilds[0]||'',status:frStatus(eptuState)},
    services:{platform:frStatus(platform),persistentUniverse:frStatus(pu),arenaCommander:frStatus(arena)},
    players:{available:false,count:null,label:'RSI ne publie pas de compteur de joueurs en ligne en temps réel.'},
    sources:{status:STATUS_URL,ptu:PTU_FAQ,liveBuild:LOANER_MATRIX}
  };
  const response=new Response(JSON.stringify(payload),{headers:{'content-type':'application/json; charset=utf-8','cache-control':'public, max-age=30, s-maxage=120, stale-while-revalidate=600','access-control-allow-origin':'*'}});
  context.waitUntil(cache.put(cacheKey,response.clone()));return response;
}
