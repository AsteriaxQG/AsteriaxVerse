import assert from 'node:assert/strict';
import fs from 'node:fs';
const catalog=fs.readFileSync(new URL('../website/shipcatalog.js',import.meta.url),'utf8');
const app=fs.readFileSync(new URL('../website/app.js',import.meta.url),'utf8');
assert.doesNotMatch(catalog,/shipPatchImpact|updateShipPatchImpact|data-ship-patch-impact/,'Ship details must not render or request patch impact');
const legacyShip=app.split('\n').find(line=>line.startsWith('function openVehicle(id)'));
assert.ok(legacyShip,'Legacy ship detail renderer must exist');
assert.doesNotMatch(legacyShip,/patchImpact\(detail\)/,'The legacy ship renderer must not restore patch impact');
console.log('PASS: patch impact removed from both ship detail renderers');
