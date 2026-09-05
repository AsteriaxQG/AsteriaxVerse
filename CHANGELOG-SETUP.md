# Changelog Asteriax Verse

Source unique : `data/changelog.json`. Chaque titre et changement contient `fr` et `en`. Versions SemVer stables X.Y.Z, uniques, triées numériquement par le serveur. Le site lit `/api/changelog`, qui embarque ce fichier au déploiement. Page : `/changelog.html`, lien sur l’accueil. Le badge est mémorisé par appareil lorsque la dernière carte entre dans l’écran.

## Configuration Cloudflare Pages, Production

- Garder le binding D1 existant `AX_DB` vers `asteriaxverse-hangar`.
- Exécuter `migrations/0002_changelog.sql` dans cette base D1 (console SQL Cloudflare).
- Ajouter le secret chiffré `DISCORD_CHANGELOG_WEBHOOK` : URL du webhook du salon Discord, sous la forme `https://discord.com/api/webhooks/ID/TOKEN`.
- Ajouter le secret chiffré `CHANGELOG_PUBLISH_TOKEN` : jeton aléatoire dédié, au moins 32 caractères, idéalement 64 caractères hexadécimaux. Ne pas réutiliser les clés Twitch.
- Redéployer après l’ajout des secrets. Aucun autre binding nécessaire. Les secrets Twitch existants ne changent pas.

Le webhook reste exclusivement dans Cloudflare. Aucun secret réel dans GitHub, les fichiers publics, les logs ou les exemples. Aucun workflow ne publie chaque commit.

## Publier une version

1. Ajouter une version dans le JSON avec les changements réels FR/EN. Ne pas modifier une version déjà annoncée ; créer une nouvelle version.
2. Déployer sur Pages et vérifier que `/api/changelog` retourne la nouvelle version.
3. Appeler `POST https://asteriaxverse.pages.dev/api/changelog/publish` avec `Authorization: Bearer <CHANGELOG_PUBLISH_TOKEN>`, depuis un outil serveur/terminal autorisé. Aucun corps nécessaire. Ne pas mettre ce jeton dans le frontend.

La route lit la dernière version du même déploiement, puis envoie un embed français avec toutes les catégories non vides et le lien vers le changelog bilingue. Elle ne prend pas de contenu arbitraire du client. Les annonces trop longues pour un embed sont refusées avant l’envoi : découper la version ou raccourcir les textes.

Le site se met à jour lors du déploiement ; Discord lors du POST suivant. Les deux services ne permettent pas une transaction simultanée. Un ajout au JSON seul n’envoie aucun message Discord.

## Anti-doublon et récupération

Une insertion D1 atomique réserve la version AVANT l’appel Discord. Deux requêtes concurrentes ne peuvent pas envoyer deux messages. Un nouvel appel retourne `alreadyPublished:true` si la version a été publiée. Le champ `contentChanged` détecte une modification d’une version déjà réservée.

En cas de délai dépassé, rejet Discord ou interruption, la réservation reste `sending` ou `uncertain`. Aucun renvoi automatique, même si Discord a accepté le message sans retourner de réponse. Cela privilégie l’absence de doublon ; la livraison ne peut pas être garantie exactement une fois entre D1 et Discord.

Vérifier le salon puis la ligne D1. Si le message existe, enregistrer son identifiant et passer la ligne en `published`. Ne supprimer une réservation pour réessayer que si l’absence du message est certaine, que la requête précédente est terminée et après vérification manuelle. Ne jamais effacer automatiquement ces réservations.

Documentation : https://developers.cloudflare.com/pages/functions/bindings/ et https://docs.discord.com/developers/resources/webhook
