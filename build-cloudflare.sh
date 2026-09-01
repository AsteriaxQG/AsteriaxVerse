#!/usr/bin/env bash
set -euo pipefail

# Prépare uniquement la version web pour Cloudflare Pages.
# Le logiciel Windows et les fichiers du projet restent inchangés.
mkdir -p website/data website/assets
cp data/asteriax_sc.db website/data/asteriax_sc.db
cp assets/asteriax_mark.png website/assets/asteriax_mark.png
cp assets/asteriax_logo.png website/assets/asteriax_logo.png

# Charge le flux d'actualités RSI automatique sans alourdir index.html.
if ! grep -q 'news.js' website/index.html; then
  sed -i 's#</body>#<script src="news.js"></script></body>#' website/index.html
fi

echo "AsteriaxVerse Web prêt dans website/"
