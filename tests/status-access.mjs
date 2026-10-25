import assert from 'node:assert/strict';
import {testEnvironment} from '../functions/api/status.js';

const now=Date.parse('2026-10-25T12:00:00Z');
const thread=(label,access,ageHours=1)=>({
  subject:`Star Citizen Alpha 4.10.3 ${label} Patch Notes 12999338 [${access}]`,
  time_created:Math.floor(now/1000-ageHours*3600),
  is_pinned:true,
  slug:`alpha-4-10-3-${label.toLowerCase()}`
});
assert.equal(testEnvironment([thread('PTU','Wave 1')],'PTU','4.10.2',now).access,'Wave 1');
assert.equal(testEnvironment([thread('PTU','Wave 5')],'PTU','4.10.2',now).access,'Wave 5');
assert.equal(testEnvironment([thread('PTU','All Waves')],'PTU','4.10.2',now).access,'All waves');
assert.equal(testEnvironment([thread('EPTU','Evocati')],'EPTU','4.10.2',now).access,'Evocati');
assert.equal(testEnvironment([thread('EPTU','Wave 1')],'EPTU','4.10.2',now).access,'Wave 1');
assert.equal(testEnvironment([thread('EPTU','Evocati',8*24)],'EPTU','4.10.2',now).status,'Non vérifié');
assert.equal(testEnvironment([{...thread('EPTU','Evocati'),is_pinned:false}],'EPTU','4.10.2',now).status,'Non vérifié');
assert.equal(testEnvironment([thread('EPTU','Evocati')],'EPTU','4.11.0',now).status,'Non vérifié');
console.log('PASS: PTU wave changes, all waves, confirmed Evocati, and stale/unverified announcements');
