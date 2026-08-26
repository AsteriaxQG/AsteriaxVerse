# Historique

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
