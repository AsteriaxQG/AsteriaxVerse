# Patch Notes Asteriax Verse

Source unique : `data/changelog.json`. Chaque titre et changement contient `fr` et `en`. Versions SemVer stables X.Y.Z, uniques, triées numériquement par le serveur. Le site lit `/api/changelog`, qui embarque ce fichier au déploiement. Page : `/changelog.html`, lien sur l’accueil. Le badge est mémorisé par appareil lorsque la dernière carte entre dans l’écran.

## Configuration Cloudflare Pages — Production

- Garder le binding D1 existant `AX_DB` vers `asteriaxverse-hangar`.
- Exécuter `migrations/0002_changelog.sql` dans cette base D1 (console SQL Cloudflare).
- Ajouter le secret chiffré `DISCORD_CHANGELOG_WEBHOOK` : URL du webhook du salon Discord, sous la forme `https://discord.com/api/webhooks/ID/TOKEN`.
- Ajouter le secret chiffré `CHANGELOG_PUBLISH_TOKEN` : jeton aléatoire dédié, au moins 32 caractères, idéalement 64 caractères hexadécimaux. Ne pas réutiliser les clés Twitch.
- Redéployer après l’ajout des secrets. Aucun autre binding nécessaire. Les secrets Twitch existants ne changent pas.

Le webhook reste exclusivement dans Cloudflare. Aucun secret réel dans GitHub, les fichiers publics, les logs ou les exemples. Aucun workflow ne publie chaque commit.

## Diagnostic avant publication

La même route possède un mode de diagnostic authentifié qui **n’envoie aucun message** et **ne réserve aucune version**. Il contrôle :

- la présence de la table D1 du changelog ;
- la dernière version détectée ;
- son état de publication (`not-published`, `sending`, `published`, `uncertain`) ;
- si le contenu a changé depuis une éventuelle réservation ;
- si le webhook Discord configuré est joignable.

Requête :

```bash
curl -X POST "https://asteriaxverse.pages.dev/api/changelog/publish" \
  -H "Authorization: Bearer $CHANGELOG_PUBLISH_TOKEN" \
  -H "X-Changelog-Action: diagnose"
```

Exemple PowerShell :

```powershell
Invoke-RestMethod -Method Post `
  -Uri "https://asteriaxverse.pages.dev/api/changelog/publish" `
  -Headers @{ Authorization = "Bearer $env:CHANGELOG_PUBLISH_TOKEN"; "X-Changelog-Action" = "diagnose" }
```

Un diagnostic prêt à publier doit notamment retourner `databaseReady: true` et `webhookReachable: true`. Un `publicationStatus: "published"` signifie que la dernière version a déjà été annoncée et ne sera pas renvoyée.

## Publier une version

1. Ajouter une nouvelle version dans `data/changelog.json` avec les changements réels FR/EN. Ne pas modifier une version déjà annoncée ; créer une nouvelle version.
2. Déployer sur Pages et vérifier que `/api/changelog` retourne la nouvelle version.
3. Exécuter le diagnostic ci-dessus.
4. Si tout est prêt, appeler `POST https://asteriaxverse.pages.dev/api/changelog/publish` avec `Authorization: Bearer <CHANGELOG_PUBLISH_TOKEN>`. Aucun corps nécessaire.

Exemple :

```bash
curl -X POST "https://asteriaxverse.pages.dev/api/changelog/publish" \
  -H "Authorization: Bearer $CHANGELOG_PUBLISH_TOKEN"
```

La route lit la dernière version du même déploiement, puis envoie un embed français avec toutes les catégories non vides et le lien vers la page bilingue. Elle ne prend pas de contenu arbitraire du client. Les annonces trop longues pour un embed sont refusées avant l’envoi : découper la version ou raccourcir les textes.

Le site se met à jour lors du déploiement ; Discord lors du POST suivant. Un ajout au JSON seul n’envoie aucun message Discord.

## Anti-doublon et récupération

Une insertion D1 atomique réserve la version **avant** l’appel Discord. Deux requêtes concurrentes ne peuvent pas envoyer deux messages. Un nouvel appel retourne `alreadyPublished:true` si la version a été publiée. Le champ `contentChanged` détecte une modification d’une version déjà réservée.

En cas de délai dépassé, rejet Discord ou interruption, la réservation reste `sending` ou `uncertain`. Aucun renvoi automatique, même si Discord a accepté le message sans retourner de réponse. Cela privilégie l’absence de doublon ; la livraison ne peut pas être garantie exactement une fois entre D1 et Discord.

Vérifier le salon puis la ligne D1. Si le message existe, enregistrer son identifiant et passer la ligne en `published`. Ne supprimer une réservation pour réessayer que si l’absence du message est certaine, que la requête précédente est terminée et après vérification manuelle. Ne jamais effacer automatiquement ces réservations.

## Test local du cœur du système

Avec une version de Node compatible avec `node:sqlite` :

```bash
node tests/changelog.mjs
```

Le test couvre l’authentification, le diagnostic D1/webhook, la protection anti-doublon, l’état `uncertain`, le tri SemVer, la validation bilingue et la génération de l’embed Discord.
