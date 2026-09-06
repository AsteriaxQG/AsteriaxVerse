import fs from 'node:fs/promises';
import {spawnSync} from 'node:child_process';

const api='https://api.github.com/repos/StarCitizenWiki/scunpacked-data/commits/master';
const headers={'Accept':'application/vnd.github+json','User-Agent':'AsteriaxVerse-data-updater'};
const commitResponse=await fetch(api,{headers});
if(!commitResponse.ok)throw Error('Unable to read upstream revision');
const commit=await commitResponse.json(),revision=commit.sha;
const message=String(commit.commit?.message||'');
const patch=message.match(/\b\d+\.\d+\.\d+-(?:LIVE|PTU|EPTU)\.\d+\b/i)?.[0];
if(!patch)throw Error('Upstream commit has no recognized patch: safe update aborted');
const current=JSON.parse(await fs.readFile('website/loadout/data/catalog.json','utf8'));
if(current.revision===revision){console.log('Loadout data already current');process.exit(0)}
await fs.mkdir('.tmp-loadout',{recursive:true});
for(const name of ['ships.json','ship-items.json']){
  const response=await fetch(`https://raw.githubusercontent.com/StarCitizenWiki/scunpacked-data/${revision}/${name}`);
  if(!response.ok)throw Error('Unable to download '+name);
  await fs.writeFile('.tmp-loadout/'+name,new Uint8Array(await response.arrayBuffer()));
}
const run=spawnSync(process.execPath,['scripts/build-loadout-data.mjs','.tmp-loadout/ships.json','.tmp-loadout/ship-items.json'],{stdio:'inherit',env:{...process.env,AX_LOADOUT_PATCH:patch,AX_LOADOUT_REVISION:revision}});
if(run.status!==0)throw Error('Catalogue generation failed');
console.log(`Updated loadout catalogue to ${patch} (${revision.slice(0,7)})`);
