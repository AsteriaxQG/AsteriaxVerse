import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import data from '../data/changelog.json' with {type:'json'};
import {publish} from '../server/changelog-publisher.js';
import {releases,embed,SITE} from '../server/changelog.js';

const sql=new DatabaseSync(':memory:');
sql.exec(readFileSync(new URL('../migrations/0002_changelog.sql',import.meta.url),'utf8'));
const db={prepare(query){return {bind(...args){return {async first(){return sql.prepare(query).get(...args)||null},async run(){return sql.prepare(query).run(...args)}}}}}};
const env={AX_DB:db,CHANGELOG_PUBLISH_TOKEN:'x'.repeat(64),DISCORD_CHANGELOG_WEBHOOK:'https://discord.com/api/webhooks/123/test'};
const request=({auth=true,action}={})=>new Request(SITE+'/api/changelog/publish',{method:'POST',headers:{...(auth?{Authorization:'Bearer '+env.CHANGELOG_PUBLISH_TOKEN}:{}),...(action?{'X-Changelog-Action':action}:{})}});

let calls=0,sends=0;
const send=async(_url,init={})=>{
  calls++;
  if((init.method||'GET').toUpperCase()==='POST'){sends++;return Response.json({id:'123'})}
  return Response.json({type:1});
};

assert.equal((await publish(request({auth:false}),env,data,send)).status,401);
assert.equal(calls,0);
assert.equal((await publish(request({action:'typo'}),env,data,send)).status,400);
assert.equal(calls,0);

const diagnosis=await (await publish(request({action:'diagnose'}),env,data,send)).json();
assert.equal(diagnosis.latestVersion,data.versions[0].version);
assert.equal(diagnosis.databaseReady,true);
assert.equal(diagnosis.publicationStatus,'not-published');
assert.equal(diagnosis.contentChanged,false);
assert.equal(diagnosis.webhookReachable,true);
assert.equal(diagnosis.webhookType,1);
assert.equal(sends,0);

const missingMigration={...env,AX_DB:{prepare(){throw Error('no table')}}};
const missing=await publish(request({action:'diagnose'}),missingMigration,data,send);
assert.equal(missing.status,503);
assert.equal((await missing.json()).databaseReady,false);

const networkFailure=await publish(request({action:'diagnose'}),env,data,async()=>{throw Object.assign(new TypeError('Illegal invocation'),{name:'TypeError'})});
assert.equal(networkFailure.status,502);
const networkBody=await networkFailure.json();
assert.equal(networkBody.databaseReady,true);
assert.equal(networkBody.webhookReachable,false);
assert.equal(networkBody.reason,'fetch binding');

const responses=await Promise.all(Array.from({length:8},()=>publish(request(),env,data,send)));
assert.equal(sends,1);
assert.ok(responses.some(r=>r.status===200));
assert.equal((await (await publish(request(),env,data,send)).json()).alreadyPublished,true);
assert.equal(sends,1);

const publishedDiagnosis=await (await publish(request({action:'diagnose'}),env,data,send)).json();
assert.equal(publishedDiagnosis.publicationStatus,'published');
assert.equal(publishedDiagnosis.contentChanged,false);

const changed=structuredClone(data);
changed.versions[0].title.fr+=' !';
const changedDiagnosis=await (await publish(request({action:'diagnose'}),env,changed,send)).json();
assert.equal(changedDiagnosis.publicationStatus,'published');
assert.equal(changedDiagnosis.contentChanged,true);

const next=structuredClone(data);
next.versions[0].version='1.2.0';
assert.equal((await publish(request(),env,next,async()=>{sends++;throw Error('timeout')})).status,502);
assert.equal((await publish(request(),env,next,send)).status,409);
assert.equal(sends,2);

const sorted={versions:[{...data.versions[0],version:'1.9.0'},{...data.versions[0],version:'1.10.0'}]};
assert.equal(releases(sorted)[0].version,'1.10.0');
assert.throws(()=>releases({versions:[data.versions[0],data.versions[0]]}));
const invalid=structuredClone(data);invalid.versions[0].date='2026-02-30';assert.throws(()=>releases(invalid));
const payload=embed(data.versions[0]);
assert.deepEqual(payload.allowed_mentions.parse,[]);
assert.ok(payload.embeds[0].fields.some(f=>f.name==='⚙️ Technique'));

console.log('PASS: auth, diagnostics, D1 readiness, webhook reachability, duplicate prevention, uncertain delivery, sorting, bilingual validation and embed');
