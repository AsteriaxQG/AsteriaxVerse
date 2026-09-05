const STATUS_URL='https://status.robertsspaceindustries.com/';
const PTU_FAQ='https://support.robertsspaceindustries.com/hc/en-us/articles/115013195927-Public-Test-Universe-PTU-FAQ';
const PTU_INSTALL='https://support.robertsspaceindustries.com/hc/en-us/articles/360000668488-Install-the-Star-Citizen-PTU';
const LOANER_MATRIX='https://support.robertsspaceindustries.com/hc/en-us/articles/360003093114-Loaner-Ship-Matrix';
const PATCH_FORUM='https://robertsspaceindustries.com/spectrum/community/SC/forum/190048?page=1&sort=newest';

function decode(s=''){return String(s).replace(/&nbsp;|&#160;/gi,' ').replace(/&amp;/gi,'&').replace(/&quot;/gi,'"').replace(/&#39;|&apos;/gi,"'").replace(/&lt;/gi,'<').replace(/&gt;/gi,'>')}
function text(html=''){return decode(html.replace(/<script[\s\S]*?<\/script>/gi,' ').replace(/<style[\s\S]*?<\/style>/gi,' ').replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim())}
async function fetchText(url){
  const sep=url.includes('?')?'&':'?';
  const fresh=`${url}${sep}asteriax_status=${Math.floor(Date.now()/60000)}`;
  const r=await fetch(fresh,{headers:{Accept:'text/html,application/xhtml+xml','Accept-Language':'en-US,en;q=0.9','User-Agent':'AsteriaxVerse/2.3'},cache:'no-store'});
  if(!r.ok)throw new Error(`${url} ${r.status}`);return r.text();
}
function escapeRe(s=''){return String(s).replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}
function serviceStatus(body,name){const re=new RegExp(`${escapeRe(name)}\\s+(Operational|Degraded Performance|Partial Outage|Major Outage|Maintenance|Degraded|Offline)`,'i');const m=body.match(re);return m?m[1]:'Unknown'}
function frStatus(v=''){const s=String(v).toLowerCase();if(s.includes('operational'))return'Opérationnel';if(s.includes('degraded'))return'Dégradé';if(s.includes('partial'))return'Incident partiel';if(s.includes('major'))return'Incident majeur';if(s.includes('maintenance'))return'Maintenance';if(s.includes('offline')||s.includes('closed'))return'Hors ligne';if(s.includes('online'))return'En ligne';if(s.includes('unknown'))return'Inconnu';return v||'Inconnu'}
function buildMatches(body,label){const re=new RegExp(`\\b(\\d+(?:\\.\\d+){1,3}-${label}\\.\\d+)\\b`,'ig');return [...body.matchAll(re)].map(m=>m[1])}
function versionOnly(build=''){return String(build).match(/^\d+(?:\.\d+){1,3}/)?.[0]||''}
function versionTuple(v=''){return String(v).split('.').map(x=>Number(x)||0)}
function compareVersions(a='',b=''){const aa=versionTuple(a),bb=versionTuple(b),n=Math.max(aa.length,bb.length);for(let i=0;i<n;i++){const d=(aa[i]||0)-(bb[i]||0);if(d)return d}return 0}
function newestVersion(values=[]){return [...new Set(values.filter(Boolean))].sort(compareVersions).pop()||''}
function versionCompatible(buildVersion='',liveVersion=''){if(!buildVersion||!liveVersion)return false;return buildVersion===liveVersion||buildVersion.startsWith(`${liveVersion}.`)||liveVersion.startsWith(`${buildVersion}.`)}
function buildSequence(build=''){return Number(String(build).match(/-(?:live|ptu|eptu)\.(\d+)/i)?.[1]||0)}
function firstMatchingBuild(builds,version=''){const unique=[...new Set(builds.filter(Boolean))];if(version){const matching=unique.filter(b=>versionCompatible(versionOnly(b),version)).sort((a,b)=>compareVersions(versionOnly(a),versionOnly(b))||buildSequence(a)-buildSequence(b));return matching.pop()||''}return unique.sort((a,b)=>compareVersions(versionOnly(a),versionOnly(b))||buildSequence(a)-buildSequence(b)).pop()||''}
function liveStatusVersion(body=''){return body.match(/LIVE STATUS\s*:\s*(\d+(?:\.\d+){1,3})/i)?.[1]||''}
function deploymentVersions(body=''){return [...body.matchAll(/(?:deploy|deployed|deployment of)\s+Star Citizen Alpha\s+(\d+(?:\.\d+){1,3})/ig)].map(m=>m[1])}
function matrixVersion(body=''){return body.match(/Last Updated:[^|]{0,120}\|\s*(\d+(?:\.\d+){1,3})-live\.\d+/i)?.[1]||''}
function ptuStateFrom(body=''){return body.match(/PTU STATUS\s*:\s*([^|]{1,50})/i)?.[1]?.trim()||''}
function environmentStatus(raw='',hasBuild=false){const s=String(raw).trim();if(hasBuild)return frStatus(s||'Online');if(!s||/unknown|not published|not available/i.test(s))return'Non publié';return frStatus(s)}
function overallFromServices(noIssues,...services){if(noIssues)return'Operational';const joined=services.join(' ');if(/Major Outage/i.test(joined))return'Major Outage';if(/Partial Outage/i.test(joined))return'Partial Outage';if(/Degraded/i.test(joined))return'Degraded';if(/Maintenance/i.test(joined))return'Maintenance';if(services.every(x=>/Operational/i.test(x)))return'Operational';return'Unknown'}

async function fetchPatchThreads(){
  const response=await fetch('https://robertsspaceindustries.com/api/spectrum/forum/channel/threads',{method:'POST',headers:{'Content-Type':'application/json','Accept':'application/json'},body:JSON.stringify({channel_id:'190048',page:1,sort:'newest'}),signal:AbortSignal.timeout(8000)});
  if(!response.ok)throw new Error(`Spectrum ${response.status}`);
  const payload=await response.json();
  if(!payload.success||!Array.isArray(payload.data?.threads))throw new Error('Spectrum indisponible');
  return payload.data.threads.filter(t=>!t.is_erased&&t.member?.meta?.badges?.some(b=>b.name==='Developer'));
}
export function testEnvironment(threads,label,liveVersion,now=Date.now()){
  const latestLive=threads.filter(t=>/\bLIVE\b.*(?:Release|Patch) Notes/i.test(t.subject)).reduce((n,t)=>Math.max(n,Number(t.time_created)||0),0);
  const candidates=threads.filter(t=>new RegExp(`\\b${label}\\b`,'i').test(t.subject)).sort((a,b)=>Number(b.time_created)-Number(a.time_created));
  const t=candidates[0];
  if(!t)return{status:'Non vérifié',version:'',build:''};
  const age=now/1000-Number(t.time_created),subject=String(t.subject);
  if(age<0||age>7*86400)return{status:'Non vérifié',version:'',build:''};
  const version=subject.match(/Alpha\s+(\d+(?:\.\d+){1,3})/i)?.[1]||'';
  const sequence=subject.match(/(?:Patch|Release) Notes\s+(\d{6,})\b/i)?.[1]||'';
  const source=`https://robertsspaceindustries.com/spectrum/community/SC/forum/190048/thread/${t.slug}`;
  if(/\b(?:offline|closed|shutdown)\b/i.test(subject))return{status:'Hors ligne',version,build:'',source};
  if(!t.is_pinned||Number(t.time_created)<=latestLive||!version||compareVersions(version,liveVersion)<0||!/\[(?:all waves|wave\s*\d+)\]/i.test(subject))return{status:'Non vérifié',version:'',build:''};
  return{status:'En ligne',version,build:sequence?`${version}-${label.toLowerCase()}.${sequence}`:'',access:/all waves/i.test(subject)?'Toutes les vagues':subject.match(/wave\s*\d+/i)?.[0]||'',source};
}

export async function onRequestGet(context){
  const cache=caches.default;
  const cacheKey=new Request(new URL('/api/status?cache=v10',context.request.url).toString());
  const cached=await cache.match(cacheKey);if(cached)return cached;
  const settled=await Promise.allSettled([fetchText(STATUS_URL),fetchText(PTU_FAQ),fetchText(PTU_INSTALL),fetchText(LOANER_MATRIX),fetchText(PATCH_FORUM),fetchPatchThreads()]);
  const statusBody=settled[0].status==='fulfilled'?text(settled[0].value):'';
  const ptuFaqBody=settled[1].status==='fulfilled'?text(settled[1].value):'';
  const ptuInstallBody=settled[2].status==='fulfilled'?text(settled[2].value):'';
  const loanerBody=settled[3].status==='fulfilled'?text(settled[3].value):'';
  const patchBody=settled[4].status==='fulfilled'?text(settled[4].value):'';

  const liveVersions=[liveStatusVersion(ptuFaqBody),liveStatusVersion(ptuInstallBody),matrixVersion(loanerBody),...deploymentVersions(statusBody),...buildMatches(statusBody,'live').map(versionOnly),...buildMatches(patchBody,'live').map(versionOnly),...buildMatches(ptuFaqBody,'live').map(versionOnly),...buildMatches(ptuInstallBody,'live').map(versionOnly)];
  const liveVersion=newestVersion(liveVersions);
  const matrixBuild=loanerBody.match(/(?:Last Updated:[^|]{0,120}\|\s*)?(\d+(?:\.\d+){1,3}-live\.\d+)/i)?.[1]||'';
  const liveBuildCandidates=[...buildMatches(statusBody,'live'),...buildMatches(patchBody,'live'),...buildMatches(ptuFaqBody,'live'),...buildMatches(ptuInstallBody,'live'),...buildMatches(loanerBody,'live'),matrixBuild];
  const liveBuild=firstMatchingBuild(liveBuildCandidates,liveVersion);

  const platform=serviceStatus(statusBody,'Platform');
  const pu=serviceStatus(statusBody,'Persistent Universe');
  const arena=serviceStatus(statusBody,'Arena Commander');
  const noIssues=/No issues detected/i.test(statusBody);
  const overall=overallFromServices(noIssues,platform,pu,arena);

  const payload={
    ok:Boolean(statusBody||ptuFaqBody||ptuInstallBody||loanerBody),
    updatedAt:new Date().toISOString(),
    live:{version:liveVersion,build:liveBuild,status:frStatus(overall)},
    ptu:testEnvironment(settled[5].status==='fulfilled'?settled[5].value:[],'PTU',liveVersion),
    eptu:testEnvironment(settled[5].status==='fulfilled'?settled[5].value:[],'EPTU',liveVersion),
    services:{platform:frStatus(platform),persistentUniverse:frStatus(pu),arenaCommander:frStatus(arena)},
    sources:{status:STATUS_URL,ptu:PATCH_FORUM,liveBuild:LOANER_MATRIX}
  };
  const response=new Response(JSON.stringify(payload),{headers:{'content-type':'application/json; charset=utf-8','cache-control':'public, max-age=15, s-maxage=60, stale-while-revalidate=120','access-control-allow-origin':'*'}});
  context.waitUntil(cache.put(cacheKey,response.clone()));return response;
}