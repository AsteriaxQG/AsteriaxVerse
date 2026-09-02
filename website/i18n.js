(()=>{
  const STORAGE_KEY='ax_language';
  const FR_TO_EN={
    "AsteriaxVerse accueil":"AsteriaxVerse home",
    "Rechercher dans AsteriaxVerse":"Search AsteriaxVerse",
    "Rechercher…":"Search…",
    "Navigation principale":"Main navigation",
    "Accueil":"Home",
    "Vaisseaux":"Ships",
    "Équipements":"Equipment",
    "Actus":"News",
    "Le Verse, plus clair.":"The Verse, clearer.",
    "Directement dans ton navigateur.":"Directly in your browser.",
    "Retrouve tous les vaisseaux Star Citizen, leur statut, leurs caractéristiques et leur disponibilité en jeu.":"Browse every Star Citizen ship, its status, specs and in-game availability.",
    "Explorer les vaisseaux":"Explore ships",
    "Voir les équipements":"View equipment",
    "Base de données":"Database",
    "Chargement…":"Loading…",
    "Dernier patch / publication":"Latest patch / post",
    "Connexion au flux officiel RSI…":"Connecting to the official RSI feed…",
    "STATUT DU VERSE":"VERSE STATUS",
    "Star Citizen en direct":"Star Citizen live",
    "Connexion RSI…":"Connecting to RSI…",
    "Récupération de l’état officiel des services et des environnements.":"Fetching the official status of services and environments.",
    "Voir les dernières actus →":"View latest news →",
    "Version officielle en cours":"Official version in progress",
    "Sources officielles RSI · actualisation automatique":"Official RSI sources · auto-refresh",
    "Vaisseaux & véhicules":"Ships & vehicles",
    "Boutiques référencées":"Referenced shops",
    "DERNIÈRES PUBLICATIONS":"LATEST POSTS",
    "Actualités Star Citizen":"Star Citizen news",
    "Les dernières publications officielles RSI, directement sur la page d’accueil.":"The latest official RSI posts, right on the home page.",
    "Voir toutes les actus →":"View all news →",
    "Chargement des dernières actualités…":"Loading latest news…",
    "NOUVEAUTÉS DU CATALOGUE":"CATALOGUE HIGHLIGHTS",
    "Vaisseaux à découvrir":"Ships to discover",
    "Les trois derniers vaisseaux ajoutés à la base AsteriaxVerse, avec leur statut et leur disponibilité d’achat.":"The three latest ships added to the AsteriaxVerse database, with their status and purchase availability.",
    "Recherche des derniers vaisseaux ajoutés…":"Finding the latest ships added…",
    "MON ESPACE":"MY SPACE",
    "Mon hangar":"My hangar",
    "Résumé uniquement, sans aperçu des cartes de vaisseaux.":"Summary only, without ship card previews.",
    "Mes vaisseaux":"My ships",
    "Liste d’envie":"Wishlist",
    "Liste d'envie":"Wishlist",
    "Ouvrir mon hangar →":"Open my hangar →",
    "EN CE MOMENT":"RIGHT NOW",
    "À suivre dans le Verse":"What’s happening in the Verse",
    "Patchs, roadmap et publications officielles récentes regroupés en un coup d’œil.":"Recent patches, roadmap updates and official posts in one glance.",
    "Chargement des informations officielles…":"Loading official information…",
    "CATALOGUE COMPLET":"FULL CATALOG",
    "CATALOGUE":"CATALOG",
    "Préparation du catalogue…":"Preparing catalog…",
    "Rechercher un vaisseau ou un constructeur":"Search a ship or manufacturer",
    "Rechercher un vaisseau, constructeur…":"Search a ship, manufacturer…",
    "Rechercher un équipement":"Search equipment",
    "Équipement":"Equipment",
    "Catalogue AsteriaxVerse":"AsteriaxVerse catalog",
    "Meilleur prix":"Best price",
    "Lieu":"Location",
    "Taille":"Size",
    "Rôles":"Roles",
    "Version":"Version",
    "Évolution prix":"Price history",
    "PATCH IMPACT":"PATCH IMPACT",
    "Où acheter":"Where to buy",
    "Prix":"Price",
    "Tous les types":"All types",
    "Véhicules terrestres":"Ground vehicles",
    "Tous les constructeurs":"All manufacturers",
    "Nom A–Z":"Name A–Z",
    "aUEC croissant":"aUEC ascending",
    "aUEC décroissant":"aUEC descending",
    "Pledge croissant":"Pledge ascending",
    "Pledge décroissant":"Pledge descending",
    "SCU décroissant":"SCU descending",
    "Toutes les sections":"All sections",
    "Toutes les tailles":"All sizes",
    "Prix croissant":"Price ascending",
    "Prix décroissant":"Price descending",
    "Classe tes vaisseaux réellement possédés séparément de ceux que tu souhaites obtenir, y compris les concepts.":"Keep ships you own separate from ships you want, including concepts.",
    "ACTUALITÉS OFFICIELLES":"OFFICIAL NEWS",
    "News Star Citizen":"Star Citizen News",
    "Dernières publications de Roberts Space Industries":"Latest posts from Roberts Space Industries",
    "Rafraîchir":"Refresh",
    "Filtres actualités":"News filters",
    "Tout":"All",
    "Vidéos":"Videos",
    "Chargement du flux officiel…":"Loading official feed…",
    "Chargement des dernières publications…":"Loading latest posts…",
    "Connexion au flux officiel Roberts Space Industries.":"Connecting to the official Roberts Space Industries feed.",
    "Ouvrir sur RSI ↗":"Open on RSI ↗",
    "Rejoins la communauté Asteriax.":"Join the Asteriax community.",
    "Créé par":"Created by",
    "Détails du catalogue":"Catalog details",
    "Fermer la fiche":"Close details",
    "Aucun équipement ne correspond à ces filtres.":"No equipment matches these filters.",
    "Aucun vaisseau ne correspond à ces filtres.":"No ship matches these filters.",
    "Aucun vaisseau enregistré dans Mes vaisseaux.":"No ships saved in My ships.",
    "Ta Liste d’envie est vide.":"Your Wishlist is empty.",
    "Aucune offre d’achat en jeu n’est actuellement référencée.":"No in-game purchase offer is currently listed.",
    "Aucune offre d’achat connue.":"No known purchase offer.",
    "Aucune publication dans cette catégorie pour le moment.":"No posts in this category yet.",
    "Le flux automatique est temporairement indisponible.":"The automatic feed is temporarily unavailable.",
    "Accède directement aux dernières publications officielles.":"Go directly to the latest official posts.",
    "FICHE VAISSEAU":"SHIP DETAILS",
    "FICHE VÉHICULE":"VEHICLE DETAILS",
    "Statut":"Status",
    "Statut RSI":"RSI status",
    "Disponibilité":"Availability",
    "Disponibilité Pledge":"Pledge availability",
    "Type":"Type",
    "Constructeur":"Manufacturer",
    "Taille RSI":"RSI size",
    "Rôle":"Role",
    "Équipage":"Crew",
    "Longueur":"Length",
    "Largeur":"Beam",
    "Hauteur":"Height",
    "Masse":"Mass",
    "Prix en jeu":"In-game price",
    "Vente Pledge":"Pledge sale",
    "Prix Pledge Store":"Pledge Store price",
    "Dernier prix Pledge":"Last Pledge price",
    "SCU":"SCU",
    "Où acheter en jeu":"Where to buy in-game",
    "Lieu d’achat en jeu":"In-game location",
    "Prix en aUEC":"Price in aUEC",
    "Voir la fiche RSI ↗":"View RSI details ↗",
    "Acheter sur RSI ↗":"Buy on RSI ↗",
    "Traduction française en cours…":"French translation in progress…",
    "Description française indisponible pour le moment.":"French description unavailable right now.",
    "Données référencées pour":"Data referenced for",
    "Aucun changement de patch référencé pour cet objet":"No patch change referenced for this item",
    "Cette zone sera alimentée par le suivi automatique des patch notes.":"This area will be powered by automatic patch-note tracking.",
    "Stable / première visite":"Stable / first visit",
    "Non renseigné":"Not specified",
    "Indisponible":"Unavailable",
    "Pas en vente":"Not currently sold",
    "Non vérifié":"Not verified",
    "Production active":"Active production",
    "Production à long terme":"Long-term production",
    "En production":"In production",
    "En concept":"In concept",
    "Statut non renseigné":"Status not provided",
    "Disponible en jeu":"Available in-game",
    "Production planifiée":"Planned production",
    "Terrestre":"Ground vehicle",
    "Vaisseau":"Ship",
    "Constructeur inconnu":"Unknown manufacturer",
    "Image en attente":"Image pending",
    "Ajouter à Mes vaisseaux":"Add to My ships",
    "Retirer de Mes vaisseaux":"Remove from My ships",
    "Ajouter à la Liste d’envie":"Add to Wishlist",
    "Retirer de la Liste d’envie":"Remove from Wishlist",
    "✓ Dans mes vaisseaux":"✓ In my ships",
    "＋ Ajouter à mes vaisseaux":"＋ Add to my ships",
    "★ Dans la Liste d’envie":"★ In wishlist",
    "☆ Ajouter à la Liste d’envie":"☆ Add to wishlist",
    "Ajouté à mes vaisseaux":"Added to My ships",
    "Retiré de mes vaisseaux":"Removed from My ships",
    "Ajouté à la Liste d’envie":"Added to Wishlist",
    "Retiré de la Liste d’envie":"Removed from Wishlist",
    "Page précédente":"Previous page",
    "Page suivante":"Next page",
    "Résultats":"Results",
    "résultat":"result",
    "résultats":"results",
    "il y a":"ago",
    "Opérationnel":"Operational",
    "Dégradé":"Degraded",
    "Hors ligne":"Offline",
    "Inconnu":"Unknown",
    "Statut indisponible":"Status unavailable",
    "Non publié":"Not published"
  };
  const EN_TO_FR=Object.fromEntries(Object.entries(FR_TO_EN).map(([fr,en])=>[en,fr]));
  const attrMemory=new WeakMap();
  let language='fr';
  let toggle;

  function preserveWhitespace(raw,replacement){const start=raw.match(/^\s*/)?.[0]||'',end=raw.match(/\s*$/)?.[0]||'';return start+replacement+end}
  function transform(raw){
    const value=raw.trim();
    if(!value)return null;
    let replacement=language==='en'?FR_TO_EN[value]:EN_TO_FR[value];
    let match;
    if(language==='en'&&(match=value.match(/^(\d[\d\s.,]*) résultat(?:s)? · page (\d+) sur (\d+)$/u)))replacement=`${match[1]} result${Number(match[1].replace(/\D/g,''))>1?'s':''} · page ${match[2]} of ${match[3]}`;
    if(language==='fr'&&(match=value.match(/^(\d[\d\s.,]*) results? · page (\d+) of (\d+)$/u)))replacement=`${match[1]} résultat${Number(match[1].replace(/\D/g,''))>1?'s':''} · page ${match[2]} sur ${match[3]}`;
    if(language==='en'&&(match=value.match(/^(\d+) vaisseau(x)?$/u)))replacement=`${match[1]} ship${Number(match[1])>1?'s':''}`;
    if(language==='fr'&&(match=value.match(/^(\d+) ships?$/u)))replacement=`${match[1]} vaisseau${Number(match[1])>1?'x':''}`;
    if(language==='en'&&(match=value.match(/^Taille\s+(.+)$/u)))replacement=`Size ${match[1]}`;
    if(language==='fr'&&(match=value.match(/^Size\s+(.+)$/u)))replacement=`Taille ${match[1]}`;
    if(language==='en'&&!replacement&&(match=value.match(/^il y a (\d+) (heure|heures|jour|jours)$/u)))replacement=`${match[1]} ${match[2].startsWith('jour')?'day':'hour'}${Number(match[1])>1?'s':''} ago`;
    if(language==='fr'&&!replacement&&(match=value.match(/^(\d+) (?:hour|hours|day|days) ago$/u)))replacement=`il y a ${match[1]} ${match[0].includes('day')?'jour':'heure'}${Number(match[1])>1?'s':''}`;
    return replacement&&replacement!==value?preserveWhitespace(raw,replacement):null;
  }
  function shouldSkip(node){const el=node.parentElement;return !el||el.closest('script,style,noscript,textarea,[data-i18n-skip],.language-toggle')}
  function translateTree(root){
    if(!root)return;
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
    const nodes=[];let node;while(node=walker.nextNode())nodes.push(node);
    nodes.forEach(textNode=>{if(shouldSkip(textNode))return;const next=transform(textNode.nodeValue);if(next)textNode.nodeValue=next});
    const elements=root.querySelectorAll?root.querySelectorAll('[placeholder],[aria-label],[title],[aria-description]'):[];
    elements.forEach(el=>{if(el.classList.contains('language-toggle'))return;['placeholder','aria-label','title','aria-description'].forEach(name=>{if(!el.hasAttribute(name))return;let original=attrMemory.get(el)?.[name];if(original===undefined){original=el.getAttribute(name);const saved=attrMemory.get(el)||{};saved[name]=original;attrMemory.set(el,saved)}const next=language==='en'?FR_TO_EN[original]||original:original;if(next!==el.getAttribute(name))el.setAttribute(name,next)})});
  }
  function syncDescriptions(){document.querySelectorAll('.ship-description').forEach(el=>{const source=el.dataset.descriptionSource,translated=el.dataset.descriptionFr;if(language==='en'&&source)el.textContent=source;else if(language==='fr'&&translated)el.textContent=translated})}
  function updateMeta(){document.documentElement.lang=language;document.title=language==='en'?'AsteriaxVerse — Star Citizen Companion':'AsteriaxVerse';const description=document.querySelector('meta[name="description"]');if(description)description.content=language==='en'?'AsteriaxVerse — Star Citizen catalog: ships, vehicles, equipment, prices, statuses, locations, manufacturers and news.':'AsteriaxVerse — catalogue Star Citizen : tous les vaisseaux, véhicules, équipements, prix, statuts, lieux, constructeurs et actualités.';if(toggle){toggle.setAttribute('aria-pressed',String(language==='en'));toggle.setAttribute('aria-label',language==='en'?'Passer le site en français':'Passer le site en anglais');toggle.querySelector('.language-code').textContent=language==='en'?'FR':'EN';toggle.querySelector('.language-label').textContent=language==='en'?'Français':'English'}}
  function apply(next){language=next==='en'?'en':'fr';try{localStorage.setItem(STORAGE_KEY,language)}catch{}updateMeta();translateTree(document.body);syncDescriptions();document.dispatchEvent(new CustomEvent('asteriax:language-change',{detail:{language}}))}
  function mount(){
    const nav=document.querySelector('.nav');if(!nav)return;
    toggle=document.createElement('button');toggle.type='button';toggle.className='language-toggle';toggle.innerHTML='<span class="language-code">EN</span><span class="language-label">English</span>';toggle.addEventListener('click',()=>apply(language==='en'?'fr':'en'));nav.insertAdjacentElement('afterend',toggle);
    const observer=new MutationObserver(records=>records.forEach(record=>{record.addedNodes.forEach(node=>{if(node.nodeType===Node.ELEMENT_NODE)translateTree(node);else if(node.nodeType===Node.TEXT_NODE&&!shouldSkip(node)){const next=transform(node.nodeValue);if(next)node.nodeValue=next}})}));observer.observe(document.body,{subtree:true,childList:true,characterData:true});
    apply(language);
  }
  try{language=localStorage.getItem(STORAGE_KEY)==='en'?'en':'fr'}catch{}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount,{once:true});else mount();
  window.AsteriaxI18n={get language(){return language},isEnglish:()=>language==='en',setLanguage:apply};
})();

