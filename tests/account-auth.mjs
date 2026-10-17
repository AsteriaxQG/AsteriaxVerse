import assert from 'node:assert/strict';
import {cleanIds,codeHash,constantTimeEqual,normalizeEmail,sessionCookie,sameOrigin,validEmail} from '../server/account-auth.js';

assert.equal(normalizeEmail('  Pilot@Example.COM  '),'pilot@example.com');
assert.equal(validEmail('pilot@example.com'),true);
assert.equal(validEmail('not-an-email'),false);
assert.deepEqual(cleanIds(['ship-1','ship-1',42]),['ship-1','42']);
assert.equal(cleanIds(new Array(1001).fill('ship')),null);
assert.equal(cleanIds(['bad\nvalue']),null);
const req={url:'https://asteriaxverse.pages.dev/api/auth/request',headers:new Headers({Origin:'https://asteriaxverse.pages.dev'})};
assert.equal(sameOrigin(req),true);
assert.equal(sameOrigin({...req,headers:new Headers({Origin:'https://attacker.example'})}),false);
assert.equal(sameOrigin({...req,headers:new Headers()}),false);
assert.match(sessionCookie('a'.repeat(64)),/Secure; HttpOnly; SameSite=Lax/);
assert.equal(constantTimeEqual('abcd','abcd'),true);
assert.equal(constantTimeEqual('abcd','abce'),false);
assert.notEqual(await codeHash('pilot@example.com','123456','secret-a'),await codeHash('pilot@example.com','123456','secret-b'));
assert.notEqual(await codeHash('pilot@example.com','123456','secret-a'),await codeHash('other@example.com','123456','secret-a'));
console.log('Email account helpers passed');

