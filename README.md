# Asteriax Verse

Application de bureau Star Citizen moderne, créée pour **AsteriaxTTV**.

La base fournie est alignée sur **Star Citizen Alpha 4.10 LIVE** et contient les vaisseaux et véhicules vendus en jeu, les composants, armes de vaisseau, armures, sous-combinaisons, armes personnelles, chargeurs et munitions, ainsi que leurs prix en aUEC et leurs lieux d'achat détaillés.

## Lancement facile sous Windows

1. Décompressez entièrement l'archive.
2. Double-cliquez sur **LANCER.bat**.
3. Au premier lancement seulement, le script crée un environnement Python et installe l'interface graphique.
4. Les lancements suivants sont immédiats.

Prérequis : Python 3.10 ou plus récent. Si Python n'est pas installé, téléchargez-le depuis [python.org](https://www.python.org/downloads/windows/) et cochez **Add Python to PATH** pendant l'installation.

## Créer le fichier `.exe`

Après avoir lancé une première fois `LANCER.bat`, double-cliquez sur **CONSTRUIRE_EXE.bat**. Le fichier portable sera créé ici :

`dist\AsteriaxVerse.exe`

Une action GitHub est aussi incluse pour construire automatiquement l'exécutable sur un véritable environnement Windows.

## Fonctions de la version 1.4.0

- 184 vaisseaux et véhicules actuellement achetables en jeu ;
- 2 796 objets achetables et 23 679 relevés de prix actifs ;
- nouveautés Alpha 4.10 intégrées : Aurora Mk II, Hull B, L-22 Alpha Wolf, Golem OX et Greycat UTV ;
- prix minimum, toutes les boutiques et chemin complet système → planète → ville/station → magasin ;
- recherche globale `Ctrl + K` dans les vaisseaux, objets et boutiques ;
- colonnes triables, filtres actifs et mémorisation des recherches ;
- pagination des grands catalogues : seules 220 lignes sont dessinées à la fois, ou 100 en mode performances ;
- recherches d’objets, de vaisseaux et de boutiques en arrière-plan, avec abandon automatique des résultats devenus obsolètes ;
- cache mémoire SQLite pour accélérer instantanément les recherches répétées ;
- index de lecture ajoutés automatiquement aux bases existantes et aux futures synchronisations ;
- filtres par famille, catégorie, fabricant, taille, système et planète ;
- navigation simplifiée autour des vaisseaux, de l'équipement de vaisseau et de l'équipement personnel ;
- textes et tableaux agrandis dans toutes les pages pour une meilleure lisibilité ;
- exploration de chaque boutique avec son inventaire complet ;
- comparaison côte à côte de quatre vaisseaux ou équipements ;
- historique des fiches récemment consultées ;
- barre latérale rétractable et interface adaptée aux fenêtres plus petites ;
- repli automatique de la barre latérale sur les fenêtres étroites, avec temporisation du redimensionnement ;
- mode performances optionnel dans **Réglages** pour les ordinateurs plus modestes ;
- fonctionnement hors ligne grâce au cache SQLite ;
- onglet **Mises à jour** séparant le logiciel et les données Star Citizen ;
- installation du logiciel suivie en quatre étapes avec confirmation après redémarrage ;
- dernière vérification, dernière installation et nouveautés visibles dans l’onglet dédié ;
- téléchargement et installation des futures versions directement dans le logiciel, sans ouvrir Chrome ;
- contrôle SHA-256 et contrôle de taille avant remplacement de l'exécutable ;
- fermeture, remplacement et redémarrage automatiques avec copie de secours ;
- pages chargées seulement à leur première ouverture et une seule page redimensionnée à la fois ;
- passage plein écran/fenêtre plus fluide avec moins de recalculs graphiques ;
- vérification des mises à jour avec retour immédiat, cache désactivé et délai d’erreur visible ;
- marques de constructeurs harmonisées (RSI, MISC, ARGO, CNOU…) et modèles récents contrôlés ;
- installation et redémarrage gérés directement par le nouvel EXE, sans script PowerShell ;
- détection discrète d'un nouveau patch LIVE et synchronisation en arrière-plan ;
- accès aux notes de patch, à l'état des serveurs, aux problèmes connus et à la roadmap RSI ;
- logo et identité **AsteriaxTTV** dans l'interface, l'écran de lancement et l'exécutable ;
- accès direct au [Discord AsteriaxTTV](https://discord.com/invite/YSK3aJwATH) et à la [chaîne Twitch](https://www.twitch.tv/asteriaxttv/about).

## Mise à jour des données

L'onglet **Mises à jour** vérifie d'abord le numéro de la version LIVE. Le bouton de synchronisation est mis en avant lorsqu'un patch plus récent est détecté, mais reste aussi disponible pour recharger tout le catalogue sans changement de version. C'est utile lorsque les inventaires communautaires sont complétés après la mise en ligne du patch. Une nouvelle base est construite séparément, contrôlée avec SQLite, puis remplace l'ancienne seulement si tout est valide. Le catalogue reste utilisable pendant cette opération et, en cas de panne réseau, le cache fonctionnel est conservé.

Pour Alpha 4.10, les cinq nouvelles ventes annoncées dans le patch officiel sont garanties dans le catalogue même pendant le délai de mise à jour du flux UEX. Une offre publiée ensuite par UEX remplace automatiquement le correctif correspondant.

Le même onglet contient le canal officiel de mise à jour d'Asteriax Verse, hébergé sur le dépôt GitHub AsteriaxTTV. À partir de la version 1.3.1, l'application télécharge elle-même le nouvel exécutable dans son dossier local, contrôle sa taille et son empreinte SHA-256, ferme l'ancienne version, remplace le fichier puis redémarre automatiquement. Les réglages et la base personnelle restent séparés dans le dossier utilisateur et sont conservés.

La version 1.3.0 ne contient pas encore ce mécanisme : son passage vers la 1.3.1 nécessite donc un dernier téléchargement manuel. Toutes les mises à jour suivantes pourront être installées directement depuis l'onglet **Mises à jour**.

### Alertes antivirus et signature Windows

Le build 1.3.1 désactive UPX et ajoute les informations de version Windows afin de limiter les faux positifs. Une alerte peut néanmoins rester possible tant que l'exécutable n'est pas signé par un certificat Authenticode reconnu. Le téléchargement intégré évite Chrome, mais ne contourne pas et ne désactive jamais Windows Defender.

Le workflow GitHub sait signer automatiquement le build lorsqu'un certificat est configuré dans les secrets `ASTERIAX_CERTIFICATE_BASE64` et `ASTERIAX_CERTIFICATE_PASSWORD`.

Les prix UEX sont communautaires. Ils peuvent évoluer après un hotfix, une remise locale ou un nouveau relevé en jeu. La version LIVE est recoupée avec les publications officielles de Roberts Space Industries.

## Structure du projet

- `main.py` : point d'entrée ;
- `ui/` : interface moderne et pages du logiciel ;
- `core/` : synchronisation, requêtes et stockage local ;
- `data/asteriax_sc.db` : instantané hors ligne validé ;
- `tests/` : contrôles automatiques de complétude ;
- `AsteriaxVerse.spec` : configuration PyInstaller.

## Sources et droits

Les sources et avertissements complets sont indiqués dans [ATTRIBUTION.md](ATTRIBUTION.md). Ce projet est un outil communautaire non officiel et n'est ni affilié ni approuvé par Cloud Imperium Games.

Créé par **AsteriaxTTV** — version 1.4.0.
