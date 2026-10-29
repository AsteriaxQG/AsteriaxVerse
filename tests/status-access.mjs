import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {testEnvironment,techPreviewFrom,mirrorLiveBuild} from '../functions/api/status.js';

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
const techRecord={channel:'TECH-PREVIEW',version:'Genesis',version_full:'Genesis Planet Tech V5',status:'ONLINE',is_active:true,updated_at:new Date(now-3600000).toISOString(),patch_notes_url:'https://robertsspaceindustries.com/spectrum/community/AVOCADO/forum/31515/thread/instancing-tech-preview'};
const mirror=record=>`<script>${JSON.stringify(record).replaceAll('"','\\"')}</script>`;
const liveRecord={channel:'LIVE',version:'4.10.2',version_full:'4.10.2-LIVE.12913470',status:'ONLINE'};
assert.equal(mirrorLiveBuild(mirror(liveRecord)),'4.10.2-live.12913470');
assert.equal(mirrorLiveBuild(mirror({...liveRecord,status:'OFFLINE'})),'');
assert.equal(mirrorLiveBuild('4.10.2-LIVE | CL 12913470'),'4.10.2-live.12913470');
assert.equal(techPreviewFrom(mirror(techRecord),now).status,'En ligne');
assert.equal(techPreviewFrom(mirror(techRecord),now).version,'Genesis');
assert.equal(techPreviewFrom(mirror({...techRecord,is_active:false}),now).status,'Hors ligne');
assert.equal(techPreviewFrom(mirror({...techRecord,updated_at:'2026-06-17T17:25:50Z'}),now).status,'Hors ligne');
assert.equal(techPreviewFrom(mirror({...techRecord,patch_notes_url:'https://example.com/fake'}),now).source,'');
assert.equal(techPreviewFrom('unavailable',now).status,'Hors ligne');
const previewEvening=Date.parse('2026-10-29T18:00:00Z');
assert.equal(techPreviewFrom('unavailable',previewEvening).status,'Evocati');
assert.equal(techPreviewFrom('unavailable',previewEvening).version,'Phase Evocati');
assert.equal(techPreviewFrom(mirror({...techRecord,is_active:true,updated_at:new Date(previewEvening-3600000).toISOString()}),previewEvening).status,'En ligne');
assert.equal(techPreviewFrom('unavailable',Date.parse('2026-11-02T23:00:00Z')).status,'Hors ligne');
const html=readFileSync(new URL('../website/index.html',import.meta.url),'utf8');
const ui=readFileSync(new URL('../website/status-ui.js',import.meta.url),'utf8');
assert.match(html,/class="verse-env tech-preview" hidden/);
assert.match(html,/id="homeTechPreviewStatus"/);
assert.match(ui,/setEnv\('TechPreview',data\.techPreview/);
assert.match(ui,/\['en ligne','evocati'\]/);
console.log('PASS: PTU wave changes, all waves, confirmed Evocati, and stale/unverified announcements');
