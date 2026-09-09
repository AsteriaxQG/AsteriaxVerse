(()=>{
  'use strict';
  const mascot=document.querySelector('[data-asteriax-mascot]');
  if(!mascot)return;
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  const finePointer=matchMedia('(hover: hover) and (pointer: fine)');

  mascot.addEventListener('pointermove',event=>{
    if(reduced.matches||!finePointer.matches)return;
    const box=mascot.getBoundingClientRect();
    const x=(event.clientX-box.left)/box.width-.5;
    const y=(event.clientY-box.top)/box.height-.5;
    mascot.style.setProperty('--mx',`${(x*12).toFixed(2)}deg`);
    mascot.style.setProperty('--my',`${(-y*10).toFixed(2)}deg`);
    mascot.style.setProperty('--gx',`${Math.round((x+.5)*100)}%`);
  });

  mascot.addEventListener('pointerleave',()=>{
    mascot.style.setProperty('--mx','0deg');
    mascot.style.setProperty('--my','0deg');
    mascot.style.setProperty('--gx','50%');
  });

  mascot.addEventListener('click',()=>{
    const speaking=mascot.classList.toggle('is-speaking');
    mascot.setAttribute('aria-expanded',String(speaking));
  });
})();

