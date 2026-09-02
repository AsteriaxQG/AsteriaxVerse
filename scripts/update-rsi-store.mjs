import {readFile,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';

const RSI='https://robertsspaceindustries.com';
const endpoint=`${RSI}/graphql`;
const matrixEndpoint=`${RSI}/ship-matrix/index`;
const output=fileURLToPath(new URL('../functions/api/ships-snapshot.js',import.meta.url));
const query='query AsteriaxPledgeStore($query: SearchQuery) { store(name: "pledge", browse: true) { listing: search(query: $query) { resources { id title url nativePrice { amount discounted discountDescription } stock { unlimited qty level } ... on TySku { isWarbond } } } } }';
const slug=value=>String(value??'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
const storeKey=value=>{const key=slug(value).replace(/\s+(?:2|10)\s+year$/,'').replace(/\s+(?:warbond|standalone ship|standalone vehicle)$/,'').replace(/[^a-z0-9]/g,'').replace(/starlifter/g,'');return({ptvbuggy:'ptv',ursarover:'ursa'}[key]||key)};
const headers={Accept:'application/json','Accept-Language':'en','User-Agent':'AsteriaxVerse-catalog-updater/1.1'};
let previousEntries=[];
try{
  const previous=await readFile(output,'utf8');
  const match=previous.match(/export const RSI_STORE_SNAPSHOT=([\s\S]+);\s*$/);
  if(match)previousEntries=JSON.parse(match[1]);
}catch{}
function officialShipUrl(path){const value=String(path||'');if(!value)return'';if(value.startsWith('http'))return value;const normalized=value.startsWith('/')?value:`/${value}`;return `${RSI}${normalized.startsWith('/en/')?normalized:`/en${normalized}`}`}
function productOffer(html){
  for(const match of String(html).matchAll(/<script\b[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi)){
    try{
      const root=JSON.parse(match[1]);
      const nodes=Array.isArray(root)?root:root?.['@graph']||[root];
      for(const node of nodes){
        if(node?.['@type']!=='Product'||!node.offers)continue;
        const offers=Array.isArray(node.offers)?node.offers:[node.offers];
        const offer=offers.find(x=>Number(x?.price)>0);
        if(offer)return{price:Number(offer.price),currency:String(offer.priceCurrency||'USD'),available:String(offer.availability||'').toLowerCase().includes('instock')};
      }
    }catch{}
  }
  return null;
}
async function mapLimit(rows,limit,work){let cursor=0;await Promise.all(Array.from({length:Math.min(limit,rows.length)},async()=>{while(cursor<rows.length){const row=rows[cursor++];await work(row)}}))}

const response=await fetch(endpoint,{method:'POST',headers:{...headers,'Content-Type':'application/json'},body:JSON.stringify({operationName:'AsteriaxPledgeStore',variables:{query:{skus:{products:['72']},limit:200,page:1,sort:{field:'weight',direction:'desc'}}},query})});
if(!response.ok)throw new Error(`Boutique RSI ${response.status}`);
const json=await response.json();
if(json.errors?.length)throw new Error(`GraphQL RSI : ${JSON.stringify(json.errors)}`);
const products=json.data?.store?.listing?.resources;
if(!Array.isArray(products)||products.length<20||products.length>=200)throw new Error(`Catalogue RSI incomplet (${products?.length??0} offres)`);
const index=new Map();
for(const product of products){
  const key=storeKey(product.title);
  if(!key)continue;
  const amount=Number(product.nativePrice?.discounted??product.nativePrice?.amount);
  const available=product.stock?.unlimited===true||Number(product.stock?.qty)>0;
  const path=String(product.url||'');
  const offer={url:path?(path.startsWith('http')?path:`${RSI}${path.startsWith('/')?path:'/'+path}`):'',title:String(product.title||''),available,price:Number.isFinite(amount)&&amount>0?amount/100:null,currency:'USD',is_warbond:product.isWarbond===true,discounted:Number(product.nativePrice?.discounted)>0,price_kind:'current'};
  const current=index.get(key);
  if(!current||(offer.available&&!current.available)||(offer.available===current.available&&offer.price!==null&&(current.price===null||offer.price<current.price)))index.set(key,offer);
}
for(const [key,offer] of previousEntries){if(!index.has(key)&&Number(offer?.price)>0)index.set(key,{...offer,available:false,is_warbond:false,discounted:false,price_kind:'historical'})}
const matrixResponse=await fetch(matrixEndpoint,{headers:{...headers,'X-Requested-With':'XMLHttpRequest'}});
if(!matrixResponse.ok)throw new Error(`RSI Ship Matrix ${matrixResponse.status}`);
const matrix=await matrixResponse.json();
if(!Array.isArray(matrix.data)||matrix.data.length<100)throw new Error(`Ship Matrix RSI incomplète (${matrix.data?.length??0} entrées)`);
const missing=new Map();
for(const ship of matrix.data){const key=storeKey(ship.name);if(key&&!index.has(key)&&ship.url&&!missing.has(key))missing.set(key,ship)}
let pageFailures=0;
await mapLimit([...missing],6,async([key,ship])=>{
  const url=officialShipUrl(ship.url);
  try{
    const page=await fetch(url,{headers:{...headers,Accept:'text/html'}});
    if(!page.ok)throw new Error(String(page.status));
    const offer=productOffer(await page.text());
    if(offer?.price>0)index.set(key,{url,title:String(ship.name||''),available:offer.available,price:offer.price,currency:offer.currency,is_warbond:false,discounted:false,price_kind:offer.available?'current':'historical'});
  }catch(error){pageFailures++;console.warn(`Prix officiel non récupéré pour ${ship.name}: ${error?.message||error}`)}
});
const entries=[...index].sort(([a],[b])=>a.localeCompare(b,'en'));
if(JSON.stringify(previousEntries)===JSON.stringify(entries)){
  console.log(`${entries.length} prix RSI vérifiés, aucun changement (${pageFailures} pages à réessayer).`);
  process.exit(0);
}
const content=`// Généré automatiquement depuis le Pledge Store officiel RSI.\nexport const RSI_STORE_SNAPSHOT_UPDATED_AT=${JSON.stringify(new Date().toISOString())};\nexport const RSI_STORE_SNAPSHOT=${JSON.stringify(entries,null,2)};\n`;
await writeFile(output,content,'utf8');
console.log(`${entries.length} prix RSI officiels enregistrés (${pageFailures} pages à réessayer).`);
