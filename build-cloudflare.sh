#!/usr/bin/env bash
set -euo pipefail

# Assemble uniquement le site statique attendu par Cloudflare Pages.
mkdir -p website/data website/assets
cp data/asteriax_sc.db website/data/asteriax_sc.db
cp assets/asteriax_mark.png website/assets/asteriax_mark.png
cp assets/asteriax_logo.png website/assets/asteriax_logo.png

# Échoue tôt si un fichier indispensable manque au lieu de publier un site incomplet.
for file in \
  website/index.html \
  website/app.js \
  website/shipcatalog.js \
  website/data/asteriax_sc.db \
  website/changelog.html \
  website/changelog.js \
  website/changelog.css \
  data/changelog.json \
  functions/api/changelog/index.js \
  functions/api/changelog/publish.js \
  server/changelog.js \
  server/changelog-publisher.js \
  migrations/0002_changelog.sql; do
  test -s "$file" || { echo "Fichier web ou changelog manquant/empty : $file" >&2; exit 1; }
done

echo "AsteriaxVerse Web + Patch Notes prêts dans website/"
