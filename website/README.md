# AsteriaxVerse Web

Version web indépendante du logiciel Windows.

## Important

Le dossier `website/` n'altère pas l'application Python, l'installateur ou les exécutables existants.

Le navigateur charge la base `../data/asteriax_sc.db` en lecture seule avec sql.js. Les données du catalogue restent donc communes au logiciel et au site dans le dépôt.

## Test local

Depuis la racine du dépôt :

```bash
python -m http.server 8080
```

Puis ouvrir `/website/` sur le serveur local.

## Publication

Le site est statique. Il peut être publié sur GitHub Pages, Cloudflare Pages, Netlify ou un autre hébergeur statique. Le répertoire publié doit conserver l'accès au dossier `data/` situé à côté de `website/` dans le dépôt.
