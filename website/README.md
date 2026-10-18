# AsteriaxVerse Web

Version web indépendante du logiciel Windows.

## Important

Le dossier `website/` n'altère pas l'application Python, l'installateur ou les exécutables existants.

Pour Cloudflare Pages, le script `build-cloudflare.sh` copie la base `data/asteriax_sc.db` dans `website/data/asteriax_sc.db` au moment du build. Le site charge ensuite cette copie en lecture seule avec sql.js.

## Test local

Depuis la racine du dépôt :

```bash
bash build-cloudflare.sh
python -m http.server 8080 -d website
```

Puis ouvrir le serveur local dans le navigateur.

## Publication Cloudflare Pages

- Build command : `bash build-cloudflare.sh`
- Build output directory : `website`
- Production branch : `main`

Le logiciel Windows et les fichiers de données d'origine restent inchangés.


## Domaine personnalisé : asteriaxverse.fr (IONOS + Cloudflare Pages)

**Adresse canonique** : https://asteriaxverse.fr — le domaine reste enregistré chez IONOS ; le site reste déployé sur **Cloudflare Pages**. Ce changement nécessite des actions DNS dans les tableaux de bord IONOS/Cloudflare, qui ne peuvent pas être effectuées par un commit GitHub.

### Avant de basculer le domaine

1. Dans **le même compte Cloudflare que le projet Pages**, ajouter `asteriaxverse.fr` comme site/zone DNS.
2. Vérifier **tous les enregistrements DNS importés**, surtout MX, SPF, DKIM, DMARC (si des adresses e-mail utilisent IONOS), ainsi que les autres sous-domaines. Les compléter dans Cloudflare **avant** de changer les serveurs de noms. Ne pas supprimer les réglages e-mail.
3. Noter les **deux serveurs de noms exacts fournis par Cloudflare** pour cette zone (ne pas en inventer).
4. Chez IONOS, ouvrir **Domaines & SSL > asteriaxverse.fr > Serveurs de noms** et choisir les serveurs personnalisés ; renseigner ceux de Cloudflare. Le domaine reste acheté et renouvelé chez IONOS. Attendre que la zone soit **Active** dans Cloudflare. La propagation DNS peut demander jusqu'à 48 heures.
5. Dans Cloudflare > **Workers & Pages > projet AsteriaxVerse > Custom domains**, cliquer sur **Set up a domain**, saisir `asteriaxverse.fr`, puis laisser Cloudflare créer l'enregistrement DNS Pages et activer le certificat HTTPS. **Ne pas pointer l'apex vers une IP arbitraire ni créer seulement un CNAME chez IONOS : l'apex Pages requiert une zone Cloudflare et ses serveurs de noms.**

### Déploiement et contrôles

1. Attendre que `https://asteriaxverse.fr/` soit **Active**, charge en HTTPS et serve le site avant de fusionner la branche de migration du domaine dans `main`. Cette branche met à jour les restrictions d'origine pour Twitch et le changelog ; la fusion trop tôt désactiverait ces fonctions sur `pages.dev`.
2. Fusionner les changements, attendre le déploiement Pages et vérifier : `/`, `/changelog.html`, `/api/news`, `/api/twitch/live`, `/api/changelog`. `/api/twitch/live` exige toujours les secrets et la base D1 déjà configurés ; ne pas partager ces secrets.
3. Pour les annonces Discord, utiliser désormais `https://asteriaxverse.fr/api/changelog/publish` et effectuer d'abord le diagnostic authentifié décrit dans `CHANGELOG-SETUP.md` (sans envoi de message).
4. Après validation, créer dans **Cloudflare Bulk Redirects** une redirection permanente **301** de `asteriaxverse.pages.dev` vers `https://asteriaxverse.fr`, en conservant chemins et paramètres de requête. Cette redirection est configurée côté Cloudflare, **pas** via `website/_redirects`.
5. Optionnel : activer aussi `www.asteriaxverse.fr` dans Cloudflare et rediriger cette variante en **301** vers l'adresse sans `www`. Ajouter le DNS proxifié requis pour cette redirection.

**Remarque Twitch** : la route publique de statut live est adaptée à la nouvelle adresse ; l'ancien flux de connexion utilisateur n'est plus actif. Si un flux OAuth est recréé, enregistrer la nouvelle URL de callback `https://asteriaxverse.fr/api/twitch/callback` dans la console développeur Twitch.

Guides de référence :
- Cloudflare Pages : https://developers.cloudflare.com/pages/configuration/custom-domains/
- Cloudflare Pages, redirection pages.dev : https://developers.cloudflare.com/pages/how-to/redirect-to-custom-domain/
- Cloudflare, redirection www : https://developers.cloudflare.com/pages/how-to/www-redirect/
- IONOS : https://www.ionos.com/help/domains/using-your-own-name-servers/using-your-own-name-servers-for-a-domain/
