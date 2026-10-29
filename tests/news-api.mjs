import assert from 'node:assert/strict';
import {parseArticles,parseMirrorArticles,mergeArticles,onRequestGet} from '../functions/api/news.js';

const title='RSI Constellation Mk V Centaurus - For Living Out There';
const path='/comm-link/transmission/21335-RSI-Constellation-Mk-V-Centaurus';
const html='<a href="'+path+'"><div class="type post">post</div><div style="background-image:url(\'//media.robertsspaceindustries.com/ship/channel_item_full.jpg\');"></div><div class="title trans-opacity">'+title+'</div><div>0 Posted: <span>3 days ago</span></div><p>RSI carries its legacy into the future.</p></a>';
const official=parseArticles(html);
assert.equal(parseArticles('<a href="/en/comm-link/transmission/21334-Alpha-4102-RSI-Discovery-Month"><h3>Star Citizen | RSI Discovery Month</h3></a>')[0].category,'NEWS');
assert.equal(parseArticles('<a href="/comm-link/Patch-Notes/21351-Star-Citizen-Alpha-4102"><h3>Star Citizen Alpha 4.10.2</h3></a>')[0].category,'PATCH');
assert.equal(official[0].title,title);assert.equal(official[0].image,'https://media.robertsspaceindustries.com/ship/channel_item_full.jpg');assert.equal(official[0].excerpt,'RSI carries its legacy into the future.');
const data={data:[{id:21335,title:'RSI Constellation Mk V Centaurus | Star Citizen',rsi_url:'https://robertsspaceindustries.com/en'+path,created_at:'2026-10-14T18:00:00+02:00',created_at_human:'3 days ago',translations:{en_EN:'A legend reborn.'},images:[{mime_type:'application/pdf',rsi_url:'https://media.robertsspaceindustries.com/ship/source.pdf'},{mime_type:'image/jpeg',rsi_url:'https://media.robertsspaceindustries.com/logo.jpg'},{mime_type:'image/jpeg',alt:'g-banner-advanced',rsi_url:'https://media.robertsspaceindustries.com/centaurus.jpg'}]},{title:'Untrusted',rsi_url:'https://example.org'+path}]};
const mirror=parseMirrorArticles(data);assert.equal(mirror.length,1);assert.equal(mirror[0].image,'https://media.robertsspaceindustries.com/centaurus.jpg');
const merged=mergeArticles(official,mirror);assert.equal(merged.length,1,'Language prefixes must not duplicate articles');assert.equal(merged[0].publishedAt,'2026-10-14T18:00:00+02:00');assert.equal(merged[0].title,title);
assert.equal(parseArticles(html.replace('href="/comm-link','href="https://example.org/comm-link')).length,0);
assert.throws(()=>parseMirrorArticles({data:null}));

const originalFetch=globalThis.fetch,originalCaches=globalThis.caches,entries=new Map(),pending=[];
globalThis.caches={default:{async match(key){return entries.get(key.url)?.clone()},async put(key,value){entries.set(key.url,value.clone())}}};
const context={request:new Request('https://example.org/api/news?refresh=1'),waitUntil:p=>pending.push(p)};
try{
  globalThis.fetch=async url=>String(url).includes('api.star-citizen.wiki')?Response.json(data):new Response('Blocked',{status:403});
  const recovered=await (await onRequestGet(context)).json();await Promise.all(pending);
  assert.equal(recovered.mode,'mirror');assert.equal(recovered.items[0].title,mirror[0].title);assert.ok(recovered.items[0].image);assert.equal(recovered.live,false);
  globalThis.fetch=async()=>{throw Error('Offline')};
  const stale=await (await onRequestGet(context)).json();await Promise.all(pending);
  assert.equal(stale.mode,'stale');assert.equal(stale.updatedAt,recovered.updatedAt);assert.equal(stale.items[0].image,recovered.items[0].image);
  entries.clear();const links=await (await onRequestGet(context)).json();assert.equal(links.mode,'links');assert.ok(links.items.length);
}finally{globalThis.fetch=originalFetch;globalThis.caches=originalCaches}
console.log('PASS: RSI card HTML, archive recovery after HTTP 403, real images, URL validation, deduplication and last-successful news during outages');
