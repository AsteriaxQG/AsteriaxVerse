import assert from 'node:assert/strict';
import vm from 'node:vm';
import fs from 'node:fs';
import {parseLauncherManifest,onRequestGet} from '../functions/api/launcher.js';

const manifest="version: 2.18.1\npath: RSI Launcher-Setup-2.18.1.exe\nreleaseDate: '2026-10-05T16:51:50.791Z'\n";
assert.equal(parseLauncherManifest(manifest).version,'2.18.1');
assert.equal(parseLauncherManifest(manifest.replaceAll('2.18.1','2.19.0')).version,'2.19.0');
assert.equal(parseLauncherManifest(manifest).publishedAt,'2026-10-05T16:51:50.791Z');
assert.throws(()=>parseLauncherManifest('version: 2.19.0-rc.1'));
assert.throws(()=>parseLauncherManifest('<html>Access denied</html>'));

const originalFetch=globalThis.fetch,originalCaches=globalThis.caches;
const saved=new Map(),pending=[];
globalThis.caches={default:{async match(key){return saved.get(key.url)?.clone()},async put(key,value){saved.set(key.url,value.clone())}}};
const context={request:new Request('https://example.org/api/launcher'),waitUntil:p=>pending.push(p)};
try{
  globalThis.fetch=async()=>new Response(manifest);
  const fresh=await (await onRequestGet(context)).json();await Promise.all(pending);
  assert.equal(fresh.version,'2.18.1');assert.equal(fresh.stale,false);
  globalThis.fetch=async()=>{throw Error('Unavailable')};
  assert.equal((await (await onRequestGet(context)).json()).version,'2.18.1','Fresh cache must serve version without a new download');
  saved.delete('https://example.org/api/launcher?cache=v1');
  const stale=await (await onRequestGet(context)).json();assert.equal(stale.stale,true);assert.equal(stale.checkedAt,fresh.checkedAt);
  saved.clear();assert.equal((await onRequestGet(context)).status,503);
}finally{globalThis.fetch=originalFetch;globalThis.caches=originalCaches}

const elements=Object.fromEntries(['#homeLauncherVersion','#homeLauncherDate','#homeLauncherLink'].map(key=>[key,{removeAttribute(){}}]));
const listeners={},timers=[];let english=false;
const page={window:{AsteriaxI18n:{isEnglish:()=>english},AsteriaxApi:{getJson:async()=>({ok:true,version:'2.18.1',publishedAt:'2026-10-05T16:51:50Z'})}},document:{querySelector:key=>elements[key],addEventListener:(key,fn)=>listeners[key]=fn,hidden:false},setInterval:fn=>timers.push(fn)};
vm.runInNewContext(fs.readFileSync(new URL('../website/launcher.js',import.meta.url),'utf8'),page);
await new Promise(resolve=>setImmediate(resolve));
assert.equal(elements['#homeLauncherVersion'].textContent,'v2.18.1');assert.match(elements['#homeLauncherDate'].textContent,/Publié le/);
english=true;listeners['asteriax:language-change']();assert.match(elements['#homeLauncherDate'].textContent,/Released on/);
page.window.AsteriaxApi.getJson=async()=>({ok:true,version:'2.19.0',publishedAt:'2026-10-18T12:00:00Z'});await timers[0]();await new Promise(resolve=>setImmediate(resolve));assert.equal(elements['#homeLauncherVersion'].textContent,'v2.19.0');
console.log('PASS: official launcher manifest, automatic new version, cache, stale fallback, missing source and FR/EN display');
