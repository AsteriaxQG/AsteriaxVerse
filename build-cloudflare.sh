#!/usr/bin/env bash
set -euo pipefail

# Assemble uniquement le site statique attendu par Cloudflare Pages.
mkdir -p website/data website/assets
cp data/asteriax_sc.db website/data/asteriax_sc.db
cp assets/asteriax_mark.png website/assets/asteriax_mark.png
cp assets/asteriax_logo.png website/assets/asteriax_logo.png

# Échoue tôt si un fichier indispensable manque au lieu de publier un site incomplet.
for file in website/index.html website/app.js website/shipcatalog.js website/data/asteriax_sc.db; do
  test -s "$file" || { echo "Fichier web manquant ou vide : $file" >&2; exit 1; }
done

echo "AsteriaxVerse Web prêt dans website/"
