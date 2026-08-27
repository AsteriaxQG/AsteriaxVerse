# Rapport de validation — Asteriax Verse 1.4.0

Contrôle effectué le **26 août 2026** sur l'instantané livré.

## Version du jeu

- version déclarée par UEX : **Star Citizen 4.10.0 LIVE** ;
- version confirmée dans les notes officielles RSI : **4.10.0-LIVE.12519617** ;
- déploiement officiel : **26 août 2026** ;
- intégrité SQLite : **OK**.

## Complétude de l'instantané

| Contrôle | Résultat |
| --- | ---: |
| Catégories UEX importées | 66 / 66 |
| Fiches d'objets importées | 7 753 |
| Objets actuellement achetables | 2 796 |
| Relevés de prix actifs pour les objets | 23 679 |
| Fiches de vaisseaux et véhicules | 280 |
| Vaisseaux et véhicules actuellement achetables | 184 |
| Offres de vaisseaux et véhicules | 301 |
| Offres 4.10 complétées pendant le délai UEX | 13 |
| Terminaux et lieux connus | 826 |
| Offres pointant vers une fiche manquante | 0 |
| Offres conservées sur un terminal hors LIVE | 0 |

Les 91 anciens relevés repérés sur des terminaux marqués hors LIVE par UEX ont été volontairement exclus du catalogue affiché.

## Familles demandées

| Famille | Objets achetables | Relevés de prix |
| --- | ---: | ---: |
| Armures | 710 | 4 280 |
| Sous-combinaisons | 105 | 574 |
| Armes personnelles, chargeurs et accessoires | 162 | 5 957 |
| Armes de vaisseau | 186 | 1 546 |
| Systèmes de vaisseau | 176 | 999 |
| Avionique | 97 | 97 |
| Propulsion | 3 | 78 |
| Utilitaires de vaisseau, minage et récupération | 84 | 1 720 |

Les catégories de vaisseau contrôlées comprennent notamment les refroidisseurs, centrales, propulseurs quantiques, boucliers, radars, lames de vol, canons, missiles, râteliers, tourelles, bombes, modules de minage, faisceaux de récupération et rayons tracteurs.

## Double contrôle des nouveautés 4.10

La note officielle RSI confirme les cinq nouvelles disponibilités en jeu. Chacune est présente dans l’instantané avec au moins un prix et une concession :

| Modèle | Prix contrôlés | Concessions |
| --- | ---: | --- |
| RSI Aurora Mk II | 904 932 à 952 560 aUEC | New Deal, Teach’s |
| MISC Hull B | 7 541 100 à 7 938 000 aUEC | New Deal, Teach’s |
| Kruger L-22 Alpha Wolf | 4 536 000 aUEC | Astro Armada |
| Drake Golem OX | 1 149 120 à 1 209 600 aUEC | New Deal, Buy and Fly (3 stations Pyro) |
| Greycat UTV | 75 600 aUEC | Astro Armada, Buy and Fly (3 stations Pyro) |

Au moment de la construction, UEX annonçait déjà la version 4.10.0 mais ne publiait encore aucune de ces 13 offres. Le logiciel complète donc uniquement ces couples modèle/concession pour 4.10. Une future offre UEX exacte reste prioritaire et n’est jamais écrasée.

## Tests automatiques

Les tests contrôlent l'intégrité de la base, la version, la couverture minimale, la résolution de chaque offre, les familles essentielles, la présence des chargeurs, les 184 véhicules, les cinq ajouts 4.10, les boutiques, la recherche globale, les itinéraires, les ressources graphiques, la compatibilité stricte des lanceurs Windows et la sécurité du mécanisme de mise à jour intégré.

La version 1.4.0 ajoute des contrôles dédiés à la création des index de performance, à l’isolation du cache de requêtes, à la pagination des trois grands catalogues, aux recherches en arrière-plan, au mode performances et à l’adaptation responsive de l’interface.

## Limite connue

Les prix sont des relevés communautaires et non une API officielle CIG. Ils peuvent évoluer après un hotfix, selon une remise locale ou après un nouveau relevé en jeu. L'onglet **Mises à jour** permet de reconstruire et revalider tout le cache même sans changement du numéro de patch.
