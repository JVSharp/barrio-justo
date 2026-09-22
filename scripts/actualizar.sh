#!/bin/zsh
# Actualización semanal: scraper + métricas geográficas de los avisos nuevos.
# La programa scripts/launchd/cl.jvsharp.barrio-justo.plist (ver README).
set -e
cd "$(dirname "$0")/../backend"
source .venv/bin/activate
echo "=== $(date '+%Y-%m-%d %H:%M') ==="
python scraper.py
python ../scripts/enriquecer_geo.py
