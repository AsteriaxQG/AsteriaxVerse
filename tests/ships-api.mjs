import assert from 'node:assert/strict';
import fs from 'node:fs';

const source=fs.readFileSync(new URL('../functions/api/ships.js',import.meta.url),'utf8');
const declaration=source.match(/async function fetchAll\(base\)\{[\s\S]*?\n\}/)?.[0];
assert.ok(declaration,'Ship API pagination helper must exist');
const fetchAll=Function('fetch',declaration+'\nreturn fetchAll')('fetch');

function response(page,{ok=true,status=200,data=[{id:page}],pages=3}={}) {
  return {ok,status,json:async()=>({data,meta:{last_page:pages}})};
}

const requested=[];
const records=await fetchAll('https://example.test/ships',async url=>{
  requested.push(url);
  const page=Number(new URL(url).searchParams.get('page[number]')||1);
  return response(page);
});
assert.deepEqual(records,[{id:1},{id:2},{id:3}]);
assert.equal(requested.length,3,'Every page must be requested');

await assert.rejects(
  fetchAll('https://example.test/ships',async url=>{
    const page=Number(new URL(url).searchParams.get('page[number]')||1);
    return response(page,{ok:page!==2,status:503});
  }),
  /page 2 503/,
  'An HTTP error on a later page must reject the whole catalog'
);

await assert.rejects(
  fetchAll('https://example.test/ships',async url=>{
    const page=Number(new URL(url).searchParams.get('page[number]')||1);
    return response(page,{data:page===3?null:[{id:page}]});
  }),
  /page 3 returned invalid data/,
  'Malformed page data must reject the whole catalog'
);

await assert.rejects(
  fetchAll('https://example.test/ships',async()=>response(1,{pages:101})),
  /invalid page count/,
  'Unreasonable page counts must be rejected'
);

console.log('PASS: ship API pagination completeness, HTTP failures and malformed responses');
