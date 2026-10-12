import assert from 'node:assert/strict';
import fs from 'node:fs';

const source=fs.readFileSync(new URL('../functions/api/ships.js',import.meta.url),'utf8');
const declaration=source.match(/async function fetchAll\(base\)\{[\s\S]*?\n\}/)?.[0];
assert.ok(declaration,'Ship API pagination helper must exist');

let mockFetch;
const fetchAll=Function('fetch',declaration+'\nreturn fetchAll')((...args)=>mockFetch(...args));
function response(page,{ok=true,status=200,data=[{id:page}],pages=3}={}) {
  return {ok,status,json:async()=>({data,meta:{last_page:pages}})};
}

const requested=[];
mockFetch=async url=>{
  requested.push(url);
  const page=Number(new URL(url).searchParams.get('page[number]')||1);
  return response(page);
};
const records=await fetchAll('https://example.test/ships');
assert.deepEqual(records,[{id:1},{id:2},{id:3}]);
assert.equal(requested.length,3,'Every page must be requested');

mockFetch=async url=>{
  const page=Number(new URL(url).searchParams.get('page[number]')||1);
  return response(page,{ok:page!==2,status:503});
};
await assert.rejects(
  fetchAll('https://example.test/ships'),
  /page 2 503/,
  'An HTTP error on a later page must reject the whole catalog'
);

mockFetch=async url=>{
  const page=Number(new URL(url).searchParams.get('page[number]')||1);
  return response(page,{data:page===3?null:[{id:page}]});
};
await assert.rejects(
  fetchAll('https://example.test/ships'),
  /page 3 returned invalid data/,
  'Malformed page data must reject the whole catalog'
);

mockFetch=async()=>response(1,{pages:101});
await assert.rejects(
  fetchAll('https://example.test/ships'),
  /invalid page count/,
  'Unreasonable page counts must be rejected'
);

console.log('PASS: ship API pagination completeness, HTTP failures and malformed responses');
