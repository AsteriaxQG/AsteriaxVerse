#!/usr/bin/env bash
set -euo pipefail

# Prépare uniquement la version web pour Cloudflare Pages.
# Le logiciel Windows et les fichiers du projet restent inchangés.
mkdir -p website/data
cp data/asteriax_sc.db website/data/asteriax_sc.db

echo "AsteriaxVerse Web prêt dans website/"
