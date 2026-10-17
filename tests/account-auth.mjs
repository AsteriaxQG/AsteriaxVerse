import assert from 'node:assert/strict';
import {cleanIds,constantTimeEqual,normalizeEmail,normalizeName,passwordHash,sessionCookie,sameOrigin,validEmail,validName,validPassword} from '../server/account-auth.js';

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
assert.equal(normalizeName('  Jean   Pilote '),'Jean Pilote');
assert.equal(validName('Jean Pilote'),true);
assert.equal(validName('x'),false);
assert.equal(validPassword('a-secure-password'),true);
assert.equal(validPassword('short'),false);
const stored=await passwordHash('correct horse battery staple','00112233445566778899aabbccddeeff');
assert.equal(stored.salt,'00112233445566778899aabbccddeeff');
assert.equal(constantTimeEqual(stored.hash,(await passwordHash('correct horse battery staple',stored.salt)).hash),true);
assert.equal(constantTimeEqual(stored.hash,(await passwordHash('wrong password 123',stored.salt)).hash),false);
console.log('Email account helpers passed');

