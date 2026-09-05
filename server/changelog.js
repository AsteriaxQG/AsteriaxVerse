export const SITE = 'https://asteriaxverse.pages.dev';
export const categories = [['new','✨ Nouveautés','✨ New'],['ui','🎨 Interface','🎨 Interface'],['fixes','🐛 Corrections','🐛 Fixes'],['technical','⚙️ Technique','⚙️ Technical']];
const localized = value => value && ['fr','en'].every(lang => typeof value[lang] === 'string' && value[lang].trim().length > 0 && value[lang].length <= 500);
export function releases(data) {
  if (!Array.isArray(data?.versions) || !data.versions.length) throw Error('Empty changelog');
  const seen = new Set();
  for (const v of data.versions) {
    if (!/^\d{1,6}\.\d{1,6}\.\d{1,6}$/.test(v.version) || seen.has(v.version)) throw Error('Invalid or duplicate version');
    seen.add(v.version);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(v.date) || !Number.isFinite(Date.parse(v.date)) || new Date(v.date).toISOString().slice(0,10) !== v.date || !localized(v.title)) throw Error('Invalid release metadata');
    for (const [key] of categories) if (!Array.isArray(v[key]) || !v[key].every(localized)) throw Error('Missing bilingual category');
  }
  return [...data.versions].sort((a,b) => {const x=a.version.split('.').map(Number),y=b.version.split('.').map(Number);return y[0]-x[0] || y[1]-x[1] || y[2]-x[2]});
}
export function embed(v) {
  const fields = [];
  for (const [key,label] of categories) {
    let value = '';
    for (const item of v[key]) {
      const line = '• ' + item.fr + '\n';
      if (value.length + line.length > 1024) {fields.push({name:label,value});value=''}
      value += line;
    }
    if(value) fields.push({name:label,value});
  }
  const result = {title:'Asteriax Verse — v'+v.version,description:v.title.fr,color:3597055,url:SITE+'/changelog.html',timestamp:v.date+'T12:00:00Z',fields,footer:{text:'Asteriax Verse · '+v.date}};
  if(fields.length>25 || JSON.stringify(result).length>5700) throw Error('Release too long for one Discord embed');
  return {allowed_mentions:{parse:[]},embeds:[result]};
}
export async function digest(value) {return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value)))].map(x=>x.toString(16).padStart(2,'0')).join('')}
