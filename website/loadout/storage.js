const key='ax_loadout_builds_v1',favoriteKey='ax_loadout_favorites_v1';
export function readBuilds(){try{const rows=JSON.parse(localStorage.getItem(key)||'[]');return Array.isArray(rows)?rows:[]}catch{return []}}
export function saveBuild(build){const rows=readBuilds().filter(b=>b.id!==build.id);if(rows.length>=50)throw Error('storageFull');localStorage.setItem(key,JSON.stringify([{...build,updatedAt:new Date().toISOString()},...rows]));}
export function deleteBuild(id){localStorage.setItem(key,JSON.stringify(readBuilds().filter(b=>b.id!==id)))}
export function favorites(){try{return new Set(JSON.parse(localStorage.getItem(favoriteKey)||'[]'))}catch{return new Set()}}
export function toggleFavorite(id){const set=favorites();set.has(id)?set.delete(id):set.add(id);localStorage.setItem(favoriteKey,JSON.stringify([...set]));return set}
