import {readFile,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';

const RSI='https://robertsspaceindustries.com';
const endpoint=`${RSI}/graphql`;
const output=fileURLToPath(new URL('../functions/api/ships-snapshot.js',import.meta.url));
const query='query AsteriaxPledgeStore($query: SearchQuery) { store(name: "pledge", browse: true) { listing: search(query: $query) { resources { id title url nativePrice { amount discounted discountDescription } stock { unlimited qty level } ... on TySku { isWarbond } } } } }';
const slug=value=>String(value??'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
const storeKey=value=>{const key=slug(value).replace(/\s+(?:2|10)\s+year$/,'').replace(/\s+(?:warbond|standalone ship|standalone vehicle)$/,'').replace(/[^a-z0-9]/g,'').replace(/starlifter/g,'');return({ptvbuggy:'ptv',ursarover:'ursa'}[key]||key)};

const response=await fetch(endpoint,{method:'POST',headers:{Accept:'application/json','Content-Type':'application/json','Accept-Language':'en','User-Agent':'AsteriaxVerse-catalog-updater/1.0'},body:JSON.stringify({operationName:'AsteriaxPledgeStore',variables:{query:{skus:{products:['72']},limit:200,page:1,sort:{field:'weight',direction:'desc'}}},query})});
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
  const offer={url:path?(path.startsWith('http')?path:`${RSI}${path.startsWith('/')?path:'/'+path}`):'',title:String(product.title||''),available,price:Number.isFinite(amount)&&amount>0?amount/100:null,currency:'USD',is_warbond:product.isWarbond===true,discounted:Number(product.nativePrice?.discounted)>0};
  const current=index.get(key);
  if(!current||(offer.available&&!current.available)||(offer.available===current.available&&offer.price!==null&&(current.price===null||offer.price<current.price)))index.set(key,offer);
}
const entries=[...index].sort(([a],[b])=>a.localeCompare(b,'en'));
let previousEntries=null;
try{
  const previous=await readFile(output,'utf8');
  const match=previous.match(/export const RSI_STORE_SNAPSHOT=([\s\S]+);\s*$/);
  if(match)previousEntries=JSON.parse(match[1]);
}catch{}
if(JSON.stringify(previousEntries)===JSON.stringify(entries)){
  console.log(`${entries.length} prix RSI vérifiés, aucun changement.`);
  process.exit(0);
}
const content=`// Généré automatiquement depuis le Pledge Store officiel RSI.\nexport const RSI_STORE_SNAPSHOT_UPDATED_AT=${JSON.stringify(new Date().toISOString())};\nexport const RSI_STORE_SNAPSHOT=${JSON.stringify(entries,null,2)};\n`;
await writeFile(output,content,'utf8');
console.log(`${entries.length} prix RSI officiels enregistrés.`);
