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
