#!/usr/bin/env bash
set -euo pipefail

# Prépare uniquement la version web pour Cloudflare Pages.
# Le logiciel Windows et les fichiers du projet restent inchangés.
mkdir -p website/data website/assets
cp data/asteriax_sc.db website/data/asteriax_sc.db
cp assets/asteriax_mark.png website/assets/asteriax_mark.png
cp assets/asteriax_logo.png website/assets/asteriax_logo.png

echo "AsteriaxVerse Web prêt dans website/"
