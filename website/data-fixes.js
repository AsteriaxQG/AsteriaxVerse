(()=>{
  const bad=/^\s*\[object Object\]\s*$/i;

  function cleanObjectText(root=document){
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
    const nodes=[];
    while(walker.nextNode()) if(bad.test(walker.currentNode.nodeValue||'')) nodes.push(walker.currentNode);
    nodes.forEach(node=>{
      const el=node.parentElement;
      if(!el)return;
      const card=el.closest('.ship-card,.vehicle-card,[data-vehicle-id]');
      const detail=el.closest('.detail-stat');
      let replacement='—';
      if(card){
        const name=card.querySelector('h3,[data-ship-name],.ship-name,.vehicle-name')?.textContent?.trim();
        if(name) replacement=name;
      }else if(detail){
        const label=detail.querySelector('span,small,.label')?.textContent?.trim()?.toLowerCase()||'';
        if(label.includes('statut')) replacement='Disponible';
        else if(label.includes('taille')) replacement='Non renseignée';
      }
      node.nodeValue=replacement;
    });
  }

  function proxyUrl(src){
    try{
      const u=new URL(src,location.href);
      if(u.origin===location.origin)return '';
      return `https://images.weserv.nl/?url=${encodeURIComponent(u.href)}&w=900&fit=contain`;
    }catch{return ''}
  }

  document.addEventListener('error',e=>{
    const img=e.target;
    if(!(img instanceof HTMLImageElement))return;
    if(!img.closest('.ship-image,.detail-vehicle-image,.ship-card,.vehicle-card'))return;
    if(img.dataset.axRetried==='1')return;
    const retry=proxyUrl(img.currentSrc||img.src);
    if(!retry)return;
    e.stopImmediatePropagation();
    img.dataset.axRetried='1';
    img.src=retry;
  },true);

  function namedFallback(root=document){
    root.querySelectorAll('.image-fallback').forEach(box=>{
      const card=box.closest('.ship-card,.vehicle-card,[data-vehicle-id]');
      const name=card?.querySelector('h3,[data-ship-name],.ship-name,.vehicle-name')?.textContent?.trim();
      if(name&&box.dataset.axNamed!=='1'){
        box.dataset.axNamed='1';
        box.innerHTML=`<strong>${name}</strong><small>Image indisponible</small>`;
      }
    });
  }

  function run(){cleanObjectText();namedFallback();}
  run();
  new MutationObserver(run).observe(document.body,{childList:true,subtree:true});
})();