(()=>{
  const bad=/^\s*\[object Object\]\s*$/i;

  function cleanTextNode(node){
    if(!bad.test(node.nodeValue||''))return;
    const el=node.parentElement;
    if(!el)return;
    const card=el.closest('.ship-card,.vehicle-card,[data-vehicle-id]');
    const detail=el.closest('.detail-stat');
    let replacement='—';
    if(card){
      const name=card.querySelector('h3,[data-ship-name],.ship-name,.vehicle-name')?.textContent?.trim();
      if(name)replacement=name;
    }else if(detail){
      const label=detail.querySelector('span,small,.label')?.textContent?.trim()?.toLowerCase()||'';
      if(label.includes('statut'))replacement='Statut non renseigné';
      else if(label.includes('taille'))replacement='Non renseignée';
    }
    node.nodeValue=replacement;
  }

  function cleanObjectText(root=document){
    if(root.nodeType===Node.TEXT_NODE){cleanTextNode(root);return}
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
    while(walker.nextNode())cleanTextNode(walker.currentNode);
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
    const boxes=[];
    if(root.matches?.('.image-fallback'))boxes.push(root);
    if(root.querySelectorAll)boxes.push(...root.querySelectorAll('.image-fallback'));
    boxes.forEach(box=>{
      const card=box.closest('.ship-card,.vehicle-card,[data-vehicle-id]');
      const name=card?.querySelector('h3,[data-ship-name],.ship-name,.vehicle-name')?.textContent?.trim();
      if(name&&box.dataset.axNamed!=='1'){
        box.dataset.axNamed='1';
        box.innerHTML=`<strong>${name}</strong><small>Image indisponible</small>`;
      }
    });
  }

  function run(root=document){cleanObjectText(root);namedFallback(root)}
  run();
  const pendingRoots=new Set();let scheduled=false;
  function schedule(root){pendingRoots.add(root);if(scheduled)return;scheduled=true;requestAnimationFrame(()=>{scheduled=false;const roots=[...pendingRoots];pendingRoots.clear();roots.forEach(run)})}
  new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(schedule))).observe(document.body,{childList:true,subtree:true});
})();
