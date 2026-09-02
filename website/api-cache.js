(()=>{
  const cached=new Map();
  const pending=new Map();
  const defaultTtl={'/api/news':120000,'/api/ships':120000,'/api/status':15000};
  const clone=value=>typeof structuredClone==='function'?structuredClone(value):JSON.parse(JSON.stringify(value));
  const canonical=input=>{const url=new URL(input,location.href);return url.origin===location.origin&&defaultTtl[url.pathname]?url.pathname:url.href};
  const storageKey=key=>`ax_api_v2:${key}`;
  function readSession(key,ttl,now){try{const hit=JSON.parse(sessionStorage.getItem(storageKey(key))||'null');return hit&&now-hit.savedAt<ttl?hit:null}catch{return null}}
  function writeSession(key,entry){try{sessionStorage.setItem(storageKey(key),JSON.stringify(entry))}catch{}}

  async function getJson(input,{force=false,ttlMs}={}){
    const key=canonical(input),ttl=Number.isFinite(ttlMs)?ttlMs:(defaultTtl[key]||30000),now=Date.now();
    if(!force){
      const hit=cached.get(key);
      if(hit&&now-hit.savedAt<ttl)return clone(hit.data);
      const stored=readSession(key,ttl,now);
      if(stored){cached.set(key,stored);return clone(stored.data)}
      if(pending.has(key))return pending.get(key).then(clone);
    }
    const task=fetch(input,{headers:{Accept:'application/json'},cache:force?'no-store':'default'})
      .then(response=>{if(!response.ok)throw new Error(`API ${response.status}`);return response.json()})
      .then(data=>{const entry={savedAt:Date.now(),data};cached.set(key,entry);writeSession(key,entry);return data})
      .finally(()=>pending.delete(key));
    pending.set(key,task);
    return task.then(clone);
  }

  window.AsteriaxApi={getJson};
})();
