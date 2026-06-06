#!/usr/bin/env python3
"""Étape (optionnelle) de résumé IA pour « Le Terminal Économies ».

Lit ``data/aggregated.json`` et, pour chaque annonce dépourvue de résumé,
demande à l'API Claude un court résumé en français (2 phrases) à partir du
titre et de l'extrait du flux. Le résultat est réécrit dans le champ
``summary`` de chaque article.

Conçu pour être **sans risque** : si la clé API est absente, si le réseau est
indisponible ou si une requête échoue, le script n'interrompt pas la
publication — il laisse simplement ``summary`` à ``null`` et l'affichage
retombe sur l'extrait du flux (géré par ``build.py``).

Variables d'environnement :
  ANTHROPIC_API_KEY   clé API (obligatoire pour générer des résumés)
  ANTHROPIC_MODEL     modèle (défaut : claude-haiku-4-5-20251001)
  SUMMARY_MAX         nombre maximum de résumés par exécution (défaut : 50)

Droit d'auteur : on ne produit qu'un résumé court et transformatif ; le texte
intégral n'est jamais recopié, et la source reste toujours créditée et liée.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGGREGATED_PATH = ROOT / "data" / "aggregated.json"

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
MAX_SUMMARIES = int(os.environ.get("SUMMARY_MAX", "50"))
TIMEOUT = 30

PROMPT = (
    "Tu es un rédacteur de presse économique. Résume l'actualité ci-dessous "
    "en deux phrases concises, neutres et claires, en français, pour un public "
    "non spécialiste. Ne reprends pas le titre mot pour mot, n'ajoute aucune "
    "phrase d'introduction ni de conclusion, ne mets pas de guillemets : "
    "renvoie uniquement le résumé.\n\nTitre : {title}\nExtrait : {excerpt}"
)


def summarize_one(title: str, excerpt: str, api_key: str) -> str | None:
    """Un appel API ; renvoie le résumé ou None en cas d'échec."""
    body = json.dumps({
        "model": MODEL,
        "max_tokens": 200,
        "messages": [{
            "role": "user",
            "content": PROMPT.format(title=title, excerpt=excerpt or title),
        }],
    }).encode("utf-8")

    req = urllib.request.Request(API_URL, data=body, method="POST", headers={
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.load(resp)
        parts = data.get("content", [])
        text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
        return text.strip() or None
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, KeyError) as exc:
        print(f"    échec résumé ({exc})")
        return None


def main() -> int:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("summarize : pas de ANTHROPIC_API_KEY — étape ignorée "
              "(repli sur les extraits du flux).")
        return 0
    if not AGGREGATED_PATH.exists():
        print("summarize : aucun aggregated.json — rien à faire.")
        return 0

    payload = json.loads(AGGREGATED_PATH.read_text(encoding="utf-8"))
    articles = payload.get("articles", [])

    todo = [a for a in articles
            if not (a.get("summary") or "").strip()
            and (a.get("excerpt") or a.get("title"))]
    todo = todo[:MAX_SUMMARIES]
    if not todo:
        print("summarize : tous les résumés sont déjà présents.")
        return 0

    print(f"summarize : génération de {len(todo)} résumé(s) via {MODEL}…")
    done = 0
    for art in todo:
        summary = summarize_one(art.get("title", ""), art.get("excerpt", ""), api_key)
        if summary:
            art["summary"] = summary
            done += 1
        time.sleep(0.4)  # politesse vis-à-vis de l'API

    if done:
        payload["articles"] = articles
        AGGREGATED_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"summarize : {done} résumé(s) écrit(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
