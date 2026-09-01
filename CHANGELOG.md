# Historique

## 1.8.0 — 1er septembre 2026

- ajout d’un sélecteur **Tableau / Galerie** dans la page Vaisseaux & véhicules ;
- nouvelle galerie en cartes modernes affichant photo, modèle, constructeur, classe, meilleur prix et lieu ;
- navigation par pages de 24 cartes pour ne jamais charger les 184 images simultanément ;
- téléchargement des photos en arrière-plan avec quatre tâches maximum ;
- cache local validé pour éviter de retélécharger les images aux lancements suivants ;
- restriction des images aux hôtes HTTPS UEX et RSI présents dans la base ;
- clic sur **Voir la fiche** ouvrant les caractéristiques et toutes les concessions sans quitter la galerie ;
- tableau affiché sur toute la largeur lorsque la fenêtre devient étroite ;
- fiche détaillée déplacée automatiquement sous le tableau en mode compact ;
- retour automatique à la disposition côte à côte dans une grande fenêtre ;
- colonnes **Constructeur** et **Meilleur prix** rééquilibrées dans les vaisseaux ;
- colonne **Taille** élargie dans les équipements, y compris en plein écran ;
- en-têtes **Constructeur** et **Meilleur prix** raccourcis en **Marque** et **Prix min.** lorsque la place manque.

## 1.7.2 — 1er septembre 2026

- conservation du format tableau pour les vaisseaux, véhicules et équipements ;
- répartition automatique et proportionnelle de la largeur entre toutes les colonnes ;
- alignement de chaque titre de colonne sur les valeurs correspondantes ;
- verrouillage du redimensionnement manuel des séparateurs pour éviter les présentations désorganisées ;
- conservation des largeurs minimales et du défilement horizontal dans les petites fenêtres ;
- recalcul temporisé des colonnes pour préserver la fluidité lors du redimensionnement.

## 1.7.1 — 1er septembre 2026

- augmentation de la police dans l’ensemble des pages ;
- taille minimale des petits textes portée à 10 px ;
- boutons, filtres, cartes et informations secondaires agrandis ;
- corps des tableaux porté à 13 px et hauteur des lignes augmentée de 40 à 44 px ;
- en-têtes de tableaux agrandis pour mieux distinguer les colonnes ;
- proportions des grands titres et navigation à sept boutons conservées.

## 1.7.0 — 1er septembre 2026

- suppression complète de l’onglet **Traduction française** ;
- navigation principale réduite de dix à sept boutons ;
- regroupement des équipements de vaisseau et personnels dans une page **Équipements** à deux sous-onglets ;
- regroupement de **Mises à jour** et **Patch & sources** dans un même espace ;
- conservation des accès rapides de l’accueil et redirection automatique des anciens onglets mémorisés ;
- sous-onglets modernes, arrondis et chargés uniquement lorsqu’ils sont utilisés.

## 1.6.2 — 1er septembre 2026

- suppression complète de la traduction classique Circuspes ;
- retrait du sélecteur de source devenu inutile ;
- Scefra devient l’unique traduction française proposée par Asteriax Verse ;
- page de traduction simplifiée avec identification claire de Scefra ;
- téléchargement autorisé uniquement depuis le dépôt officiel SPEED0U/Scefra ;
- traduction limitée au canal LIVE tant que Scefra ne publie pas de version PTU dédiée.

## 1.6.1 — 1er septembre 2026

- remplacement de la traduction proposée par défaut par **Scefra**, une autre base française corrigée par sa communauté ;
- ajout d’un sélecteur permettant de choisir entre Scefra et la traduction classique Circuspes ;
- conservation automatique de la source choisie entre les lancements ;
- indication claire que Scefra est réservée au canal LIVE et peut encore présenter quelques problèmes d’accents ;
- affichage de la source réellement installée dans l’état de la traduction ;
- barre de navigation redessinée d’après la référence fournie : grand panneau arrondi et onglets sous forme de cartes séparées ;
- coins plus arrondis, contours fins, espacements plus généreux et sélection active mise en évidence ;
- nouveau style conservé lorsque la barre latérale est repliée.

## 1.6.0 — 31 août 2026

- nouvel onglet **Traduction française** dans la navigation principale ;
- détection automatique du dossier Star Citizen et des canaux LIVE, PTU, EPTU, HOTFIX et TECH-PREVIEW ;
- installation et mise à jour en un clic du pack français communautaire maintenu par Dymerz / StarCitizen-Localization ;
- téléchargement en arrière-plan avec progression, sans lancer PowerShell ni ouvrir le navigateur ;
- contrôle HTTPS strict, limite de taille et validation de la structure de `global.ini` avant installation ;
- sauvegarde unique des fichiers `global.ini` et `user.cfg` existants avant la première modification ;
- bouton **Restaurer l’anglais** rétablissant exactement les fichiers sauvegardés ;
- conservation des autres réglages présents dans `user.cfg` ;
- aucune modification des exécutables du jeu ni d’Easy Anti-Cheat ;
- ajout de tests automatiques couvrant l’installation, la mise à jour, la restauration et les redirections non autorisées.

## 1.5.1 — 28 août 2026

- ajout d’une classe précise à chacun des 184 vaisseaux et véhicules achetables ;
- distinction entre chasseurs parasites, légers, moyens et lourds ;
- transports de fret répartis selon leur capacité ;
- classifications dédiées pour le combat, l’exploration, le minage, la récupération, le médical et les autres spécialités ;
- ajout du filtre **Classe** dans la page Vaisseaux & véhicules ;
- remplacement de la colonne générique **Type** par la colonne plus informative **Classe** ;
- classe affichée dans les fiches, le comparateur et la recherche globale ;
- taxonomie des chasseurs recoupée avec Star Citizen Wiki.

## 1.5.0 — 27 août 2026

- comparateur recentré sur trois éléments pour conserver des cartes lisibles ;
- détection automatique du meilleur prix et du plus grand cargo ;
- affichage de l’écart avec l’option la moins chère ;
- date et indicateur de fiabilité ajoutés à chaque prix dans les fiches et le comparateur ;
- tableau des actualités LIVE intégré à l’accueil, sans créer d’onglet redondant ;
- accès à la source officielle par double-clic sur une actualité ;
- éléments consultés récemment proposés dans la recherche globale ;
- résumé des changements de quantité après la synchronisation du catalogue.

## 1.4.3 — 27 août 2026

- centrage des prix sous leurs en-têtes dans tous les tableaux ;
- centrage des lieux pour mieux les séparer des montants ;
- alignement homogène appliqué aux équipements, vaisseaux, boutiques et résultats de recherche.

## 1.4.2 — 27 août 2026

- suppression du cadre intérieur carré des tableaux natifs Windows ;
- ajout d’une surface intérieure arrondie cohérente avec les cartes de l’application ;
- en-têtes de colonnes plus aérés et visuellement mieux intégrés ;
- repositionnement des barres de défilement dans la nouvelle surface ;
- boutons de pagination arrondis et harmonisés avec le reste de l’interface ;
- amélioration appliquée à tous les tableaux des différents onglets.

## 1.4.1 — 27 août 2026

- ajout d’un véritable installateur Windows construit avec Inno Setup ;
- installation par utilisateur dans `%LOCALAPPDATA%\Programs\Asteriax Verse`, sans droits administrateur ;
- création des raccourcis du Menu Démarrer et du Bureau ;
- ajout automatique dans la liste **Applications installées** de Windows ;
- désinstalleur propre conservant volontairement la base et les préférences personnelles ;
- lancement proposé à la fin de l’installation ;
- publication automatique de `AsteriaxVerse-Setup.exe` et de son manifeste SHA-256 sur GitHub ;
- signature Authenticode de l’application et de l’installateur lorsque le certificat facultatif est configuré ;
- maintien de l’auto-updater direct dans le dossier installé.

## 1.4.0 — 27 août 2026

- pagination des catalogues d’objets, de vaisseaux et de boutiques pour éviter le rendu simultané de milliers de lignes ;
- recherches SQLite exécutées hors du fil graphique, avec résultats obsolètes automatiquement ignorés ;
- cache mémoire protégé pour accélérer les recherches répétées sans partager d’objets modifiables ;
- nouveaux index de lecture appliqués aux bases existantes et créés pendant chaque synchronisation ;
- conservation du tri et des filtres entre les sessions ;
- nouveau **Mode performances** limitant chaque page à 100 lignes et supprimant les animations non essentielles ;
- barre latérale automatiquement repliée sur une petite fenêtre puis restaurée selon la préférence de l’utilisateur ;
- temporisation des recalculs de mise en page pour fluidifier le passage plein écran/fenêtre ;
- suppression des doubles recherches lors de l’ouverture directe d’une fiche.

## 1.3.6 — 27 août 2026

- progression de l’installation présentée en quatre étapes clairement identifiées ;
- création d’un marqueur de réussite par le nouvel EXE avant le redémarrage ;
- confirmation unique « mise à jour installée avec succès » après la relance ;
- affichage de la dernière vérification et de la dernière installation ;
- bouton **Voir les nouveautés** directement dans l’onglet **Mises à jour**.

## 1.3.5 — 27 août 2026

- suppression complète du script PowerShell bloqué sur certaines configurations Windows ;
- lancement du nouvel EXE dans un mode de mise à jour intégré et autonome ;
- attente de la fermeture, remplacement atomique puis redémarrage sans interpréteur externe ;
- contrôle SHA-256 avant et après la copie ;
- journal créé dès le lancement et restauration automatique de l’ancienne version en cas d’échec.

## 1.3.4 — 27 août 2026

- remplacement de **Roberts Space Industries** par la marque officielle **RSI** ;
- normalisation des constructeurs en marques courtes : MISC, ARGO, CNOU, Aegis, Anvil, Drake, etc. ;
- correction de l’entité HTML affichée dans **Grey's Market** ;
- contrôle explicite des modèles récents ou faciles à confondre (Hermes, Meteor, Salvation, Clipper, MOTH, MTC, Shiv, Hull B…) ;
- filtres constructeur compatibles avec l’ancienne base et les futures synchronisations UEX.

## 1.3.3 — 27 août 2026

- retour visuel immédiat lorsque l’utilisateur clique sur **Vérifier maintenant** ;
- ajout d’un délai de 15 secondes avec message explicite si le réseau ne répond pas ;
- contournement des copies périmées du manifeste GitHub avec cache désactivé ;
- transfert du résultat réseau vers l’interface par une file sûre pour Tkinter ;
- bouton **Réessayer** automatiquement réactivé après une erreur ou un délai dépassé.

## 1.3.2 — 27 août 2026

- chargement des pages à la demande au lieu de construire les dix écrans au démarrage ;
- retrait de la grille pour chaque page invisible afin qu’une seule interface soit redimensionnée ;
- réduction des recalculs CustomTkinter lors du passage en plein écran ou du retour en fenêtre ;
- démarrage plus léger et navigation conservant l’état des pages déjà ouvertes.

## 1.3.1 — 26 août 2026

- remplacement de l'ouverture de Chrome par une mise à jour directement intégrée au logiciel ;
- téléchargement en arrière-plan avec progression visible dans l'onglet **Mises à jour** ;
- validation obligatoire de la taille, de l'origine GitHub et de l'empreinte SHA-256 ;
- remplacement de l'exécutable après fermeture, copie de secours et redémarrage automatique ;
- désactivation d'UPX et ajout des métadonnées Windows pour réduire les faux positifs antivirus ;
- prise en charge facultative de la signature Authenticode dans GitHub Actions ;
- publication atomique de l'EXE et de son manifeste d'intégrité par le workflow Windows.

## 1.3.0 — 26 août 2026

- navigation recentrée sur les fonctions essentielles ;
- suppression des onglets **Mes favoris**, **Liste de courses** et **Planificateur de loadout** ;
- retrait de l'onglet redondant **Tous les objets**, tout en conservant la recherche globale complète ;
- retrait des actions liées aux favoris, aux listes de courses et aux loadouts dans les fiches ;
- agrandissement uniforme des textes, titres, filtres et tableaux dans toutes les pages ;
- suppression du bouton redondant **Vérifier les mises à jour** dans **Patch & sources**.

## 1.2.1 — 26 août 2026

- activation du canal officiel de mise à jour du logiciel via le dépôt GitHub AsteriaxVerse ;
- ajout du manifeste `UPDATE_MANIFEST.json` prêt pour les prochaines versions ;
- remplacement de l'état « Canal à configurer » par une véritable vérification en ligne ;
- téléchargement toujours manuel et contrôlé : le logiciel n'exécute jamais automatiquement un fichier reçu.

## 1.2.0 — 26 août 2026

- instantané hors ligne mis à jour vers Star Citizen Alpha 4.10 LIVE ;
- ajout vérifié de l’Aurora Mk II, du MISC Hull B, du Kruger L-22 Alpha Wolf, du Drake Golem OX et du Greycat UTV ;
- ajout des 13 offres correspondantes avec prix aUEC et concessions de Stanton, Pyro et Nyx ;
- bouton « Actualiser tout le catalogue » désormais toujours disponible, même lorsque le numéro du patch ne change pas ;
- correctif automatique du délai de publication UEX : les offres officielles 4.10 manquantes sont complétées sans écraser les futures données du fournisseur ;
- résumé des nouveautés de catalogue Alpha 4.10 et lien direct vers le patch officiel dans l’onglet Mises à jour ;
- tests de complétude étendus aux cinq nouvelles ventes 4.10.

## 1.1.1 — 24 août 2026

- texte de la barre latérale gauche agrandi pour améliorer la lisibilité ;
- largeur et espacement de la navigation ajustés aux nouveaux libellés ;
- boutons Discord et Twitch rendus plus lisibles.

## 1.1.0 — 23 août 2026

- intégration du nouveau logo HD AsteriaxTTV dans l'interface, le splash screen et l'icône Windows ;
- ajout des liens Discord et Twitch officiels ;
- recherche globale `Ctrl + K` pour les vaisseaux, objets et boutiques ;
- tableaux triables, filtres actifs et préférences mémorisées ;
- nouvel explorateur de boutiques avec inventaire complet ;
- liste de courses avec quantités, budget et itinéraire d'achat ;
- comparateur de quatre vaisseaux ou équipements ;
- planificateur de loadout avec estimation du coût ;
- historique des fiches consultées ;
- navigation rétractable et interface plus adaptable ;
- onglet dédié aux mises à jour du logiciel et aux données du jeu ;
- détection d'un nouveau patch LIVE et synchronisation non bloquante ;
- canal HTTPS prêt pour les futures mises à jour officielles du logiciel ;
- extension des tests automatiques à 14 contrôles.

## 1.0.1 — 23 août 2026

- correction des fins de ligne des scripts Windows en CRLF ;
- scripts `LANCER.bat` et `CONSTRUIRE_EXE.bat` convertis en ASCII pour fonctionner avec toutes les pages de codes de `cmd.exe` ;
- messages d'installation et détection de Python rendus plus robustes.

## 1.0.0 — 23 août 2026

- première version publique d'Asteriax Verse ;
- instantané complet Star Citizen 4.9 LIVE ;
- catalogue des 179 vaisseaux et véhicules achetables en jeu ;
- catalogue de 2 791 objets achetables ;
- prix aUEC et boutiques détaillées ;
- recherche, filtres, favoris et cache hors ligne ;
- synchronisation complète UEX avec validation atomique ;
- scripts Windows pour lancer l'application et construire le `.exe`.
