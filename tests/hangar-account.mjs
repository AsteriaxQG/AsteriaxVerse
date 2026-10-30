import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {onRequest} from '../functions/api/account/[action].js';

const sqlite=new DatabaseSync(':memory:');
const db={prepare(sql){const statement=sqlite.prepare(sql);return {bind(...args){return {run:async()=>statement.run(...args),first:async()=>statement.get(...args)||null,all:async()=>({results:statement.all(...args)})}},run:async()=>statement.run()}}};
const origin='https://asteriaxverse.fr';
async function call(action,method='GET',data,cookie=''){
  const request=new Request(`${origin}/api/account/${action}`,{method,headers:{...(method==='POST'?{'origin':origin,'content-type':'application/json'}:{}),...(cookie?{'cookie':cookie}:{})},body:data?JSON.stringify(data):undefined});
  const response=await onRequest({request,env:{AX_DB:db},params:{action}});
  return {response,data:await response.json()};
}
const created=await call('register','POST',{name:'Compte test',email:'test@example.invalid',password:'motdepasse-test-123'});
assert.equal(created.response.status,200,JSON.stringify(created.data));
const cookie=created.response.headers.get('set-cookie').split(';')[0];
assert.equal((await call('hangar','POST',{id:'ship-1',status:'owned'},cookie)).response.status,200);
assert.equal((await call('hangar','POST',{id:'ship-2',status:'wishlist'},cookie)).response.status,200);
assert.equal((await call('hangar','POST',{id:'ship-1',insurance:'lti'},cookie)).response.status,200);
let session=await call('session','GET',undefined,cookie);
assert.deepEqual(session.data.hangar,{owned:['ship-1'],wishlist:['ship-2'],insurance:{'ship-1':'lti'}});
assert.equal((await call('hangar','POST',{id:'ship-1',status:'none'},cookie)).response.status,200);
session=await call('session','GET',undefined,cookie);
assert.deepEqual(session.data.hangar,{owned:[],wishlist:['ship-2'],insurance:{'ship-1':'lti'}});
console.log('Hangar account flow OK');
