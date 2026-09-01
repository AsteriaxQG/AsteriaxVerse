#!/usr/bin/env bash
set -euo pipefail

# Prépare uniquement la version web pour Cloudflare Pages.
# Le logiciel Windows et les fichiers du projet restent inchangés.
mkdir -p website/data website/assets
cp data/asteriax_sc.db website/data/asteriax_sc.db
cp assets/asteriax_mark.png website/assets/asteriax_mark.png
cp assets/asteriax_logo.png website/assets/asteriax_logo.png

# Force le navigateur à charger les dernières corrections du catalogue.
sed -i 's/shipcatalog.js?v=4/shipcatalog.js?v=5/g' website/index.html
sed -i 's/verified-status.js?v=2/verified-status.js?v=3/g' website/index.html
sed -i 's/vehiclefilters.js?v=1/vehiclefilters.js?v=2/g' website/index.html

# Bandeau d'état du Verse : retire le compteur joueurs non disponible,
# passe les services sur trois colonnes et force les nouveaux assets.
sed -i 's#<div><span>Joueurs en ligne</span><strong id="homePlayers">Non publié</strong></div>##g' website/index.html
sed -i 's/grid-template-columns:repeat(4,minmax(0,1fr))/grid-template-columns:repeat(3,minmax(0,1fr))/g' website/home.css
sed -i 's/home.css?v=2/home.css?v=3/g' website/index.html
sed -i 's/home.js?v=2/home.js?v=3/g' website/index.html
if ! grep -q 'status-ui.css' website/index.html; then
  sed -i 's#</head>#<link rel="stylesheet" href="status-ui.css?v=1"/></head>#' website/index.html
fi
if ! grep -q 'status-ui.js' website/index.html; then
  sed -i 's#</body>#<script src="status-ui.js?v=2"></script></body>#' website/index.html
else
  sed -i 's/status-ui.js?v=1/status-ui.js?v=2/g' website/index.html
fi

# Trie "À suivre dans le Verse" du plus récent au plus ancien.
if ! grep -q 'home-now-order.js' website/index.html; then
  sed -i 's#</body>#<script src="home-now-order.js?v=1"></script></body>#' website/index.html
fi

# Rend la flèche du dernier patch cliquable et garde une actualisation automatique.
if ! grep -q 'patch-refresh.css' website/index.html; then
  sed -i 's#</head>#<link rel="stylesheet" href="patch-refresh.css?v=2"/></head>#' website/index.html
else
  sed -i 's/patch-refresh.css?v=1/patch-refresh.css?v=2/g' website/index.html
fi
if ! grep -q 'patch-refresh.js' website/index.html; then
  sed -i 's#</body>#<script src="patch-refresh.js?v=2"></script></body>#' website/index.html
else
  sed -i 's/patch-refresh.js?v=1/patch-refresh.js?v=2/g' website/index.html
fi

# Charge le flux d'actualités RSI automatique sans alourdir index.html.
if ! grep -q 'news.js' website/index.html; then
  sed -i 's#</body>#<script src="news.js"></script></body>#' website/index.html
fi

echo "AsteriaxVerse Web prêt dans website/"
