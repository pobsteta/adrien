#!/usr/bin/env bash
#
# publish.sh — régénère « La Quotidienne Éco » de bout en bout.
#
#   1. aggregate.py  : récupère les flux RSS -> data/aggregated.json
#   2. summarize.py  : résumés IA (optionnel, si ANTHROPIC_API_KEY)
#   3. build.py      : assemble auto + manuel -> site statique dans output/
#
# Usage :
#   ./publish.sh                  # édition du jour
#   ./publish.sh 2026-06-06       # force une date d'édition (archive datée)
#
set -euo pipefail

# Se placer à la racine du projet, quel que soit le répertoire d'appel.
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
EDITION_DATE="${1:-}"

echo "════════════════════════════════════════════"
echo "  La Quotidienne Éco — publication"
echo "════════════════════════════════════════════"

echo "[1/3] Agrégation des flux RSS…"
"$PYTHON" scripts/aggregate.py

echo
echo "[2/3] Résumés IA (optionnel : nécessite ANTHROPIC_API_KEY)…"
"$PYTHON" scripts/summarize.py || echo "  (étape résumé ignorée)"

echo
echo "[3/3] Génération du site statique…"
if [ -n "$EDITION_DATE" ]; then
  "$PYTHON" scripts/build.py "$EDITION_DATE"
else
  "$PYTHON" scripts/build.py
fi

echo
echo "✓ Site prêt dans ./output/  (ouvrez output/index.html)"
