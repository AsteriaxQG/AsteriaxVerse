const STATUS_URL='https://status.robertsspaceindustries.com/';
const PTU_FAQ='https://support.robertsspaceindustries.com/hc/en-us/articles/115013195927-Public-Test-Universe-PTU-FAQ';
const LOANER_MATRIX='https://support.robertsspaceindustries.com/hc/en-us/articles/360003093114-Loaner-Ship-Matrix';
const PATCH_FORUM='https://robertsspaceindustries.com/spectrum/community/SC/forum/190048?page=1&sort=newest';

function decode(s=''){return String(s).replace(/&nbsp;|&#160;/gi,' ').replace(/&amp;/gi,'&').replace(/&quot;/gi,'"').replace(/&#39;|&apos;/gi,"'").replace(/&lt;/gi,'<').replace(/&gt;/gi,'>')}
function text(html=''){return decode(html.replace(/<script[\s\S]*?<\/script>/gi,' ').replace(/<style[\s\S]*?<\/style>/gi,' ').replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim())}
async function fetchText(url){const r=await fetch(url,{headers:{Accept:'text/html,application/xhtml+xml','Accept-Language':'en-US,en;q=0.9','User-Agent':'AsteriaxVerse/2.1'}});if(!r.ok)throw new Error(`${url} ${r.status}`);return r.text()}
function escapeRe(s=''){return String(s).replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}
function serviceStatus(body,name){const re=new RegExp(`${escapeRe(name)}\\s+(Operational|Degraded Performance|Partial Outage|Major Outage|Maintenance|Degraded|Offline)`,'i');const m=body.match(re);return m?m[1]:'Unknown'}
function frStatus(v=''){const s=String(v).toLowerCase();if(s.includes('operational'))return'Opérationnel';if(s.includes('degraded'))return'Dégradé';if(s.includes('partial'))return'Incident partiel';if(s.includes('major'))return'Incident majeur';if(s.includes('maintenance'))return'Maintenance';if(s.includes('offline'))return'Hors ligne';if(s.includes('online'))return'En ligne';return v||'Inconnu'}
function buildMatches(body,label){const re=new RegExp(`\\b(\\d+(?:\\.\\d+){1,3}-${label}\\.\\d+)\\b`,'ig');return [...body.matchAll(re)].map(m=>m[1])}
function versionOnly(build=''){return String(build).match(/^\d+(?:\.\d+){1,3}/)?.[0]||''}
function firstMatchingBuild(builds,version=''){const unique=[...new Set(builds.filter(Boolean))];if(version){const match=unique.find(b=>versionOnly(b)===version);if(match)return match;return''}return unique[0]||''}
function overallFromServices(noIssues,...services){if(noIssues)return'Operational';const joined=services.join(' ');if(/Major Outage/i.test(joined))return'Major Outage';if(/Partial Outage/i.test(joined))return'Partial Outage';if(/Degraded/i.test(joined))return'Degraded';if(/Maintenance/i.test(joined))return'Maintenance';if(services.every(x=>/Operational/i.test(x)))return'Operational';return'Unknown'}

export async function onRequestGet(context){
  const cache=caches.default;
  const cacheKey=new Request(new URL('/api/status?cache=v4',context.request.url).toString());
  const cached=await cache.match(cacheKey);if(cached)return cached;
  const settled=await Promise.allSettled([fetchText(STATUS_URL),fetchText(PTU_FAQ),fetchText(LOANER_MATRIX),fetchText(PATCH_FORUM)]);
  const statusBody=settled[0].status==='fulfilled'?text(settled[0].value):'';
  const ptuBody=settled[1].status==='fulfilled'?text(settled[1].value):'';
  const loanerBody=settled[2].status==='fulfilled'?text(settled[2].value):'';
  const patchBody=settled[3].status==='fulfilled'?text(settled[3].value):'';

  const ptuHeader=ptuBody.match(/PTU STATUS:\s*([^|]{1,40})\|\s*LIVE STATUS:\s*([\d.]+)/i);
  const officialLiveVersion=(ptuHeader?.[2]||'').trim();
  const matrixBuild=loanerBody.match(/Last Updated:[^|]{0,100}\|\s*(\d+(?:\.\d+){1,3}-live\.\d+)/i)?.[1]||'';
  const liveBuildCandidates=[...buildMatches(patchBody,'live'),...buildMatches(statusBody,'live'),...buildMatches(ptuBody,'live'),matrixBuild];
  const liveBuild=firstMatchingBuild(liveBuildCandidates,officialLiveVersion);
  const liveVersion=officialLiveVersion||versionOnly(firstMatchingBuild(liveBuildCandidates));

  const ptuBuilds=[...buildMatches(patchBody,'ptu'),...buildMatches(ptuBody,'ptu')];
  const eptuBuilds=[...buildMatches(patchBody,'eptu'),...buildMatches(ptuBody,'eptu')];
  const ptuState=(ptuHeader?.[1]||'').trim()||(ptuBuilds.length?'Online':'Unknown');
  const eptuState=eptuBuilds.length?'Online':'Non publié';

  const platform=serviceStatus(statusBody,'Platform');
  const pu=serviceStatus(statusBody,'Persistent Universe');
  const arena=serviceStatus(statusBody,'Arena Commander');
  const noIssues=/No issues detected/i.test(statusBody);
  const overall=overallFromServices(noIssues,platform,pu,arena);

  const payload={
    ok:Boolean(statusBody||ptuBody||loanerBody),
    updatedAt:new Date().toISOString(),
    live:{version:liveVersion,build:liveBuild,status:frStatus(overall)},
    ptu:{version:versionOnly(ptuBuilds[0]||''),build:ptuBuilds[0]||'',status:frStatus(ptuState)},
    eptu:{version:versionOnly(eptuBuilds[0]||''),build:eptuBuilds[0]||'',status:frStatus(eptuState)},
    services:{platform:frStatus(platform),persistentUniverse:frStatus(pu),arenaCommander:frStatus(arena)},
    sources:{status:STATUS_URL,ptu:PTU_FAQ,liveBuild:LOANER_MATRIX}
  };
  const response=new Response(JSON.stringify(payload),{headers:{'content-type':'application/json; charset=utf-8','cache-control':'public, max-age=20, s-maxage=90, stale-while-revalidate=300','access-control-allow-origin':'*'}});
  context.waitUntil(cache.put(cacheKey,response.clone()));return response;
}
