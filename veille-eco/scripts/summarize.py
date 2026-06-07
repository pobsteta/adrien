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
    "Tu es un rédacteur de presse économique pour un terminal utilisé par des "
    "traders professionnels. À partir du titre et de l'extrait ci-dessous, "
    "rédige un RÉSUMÉ COMPLET, riche, CHIFFRÉ et autonome (le lecteur ne doit "
    "pas avoir besoin d'ouvrir l'article d'origine) : 6 à 8 paragraphes "
    "DÉVELOPPÉS de 2 à 4 phrases chacun. Sois quantitatif et précis : intègre "
    "autant que possible des chiffres concrets (pourcentages, niveaux, "
    "variations en glissement mensuel/annuel, montants, dates, comparaison au "
    "consensus et au précédent), et nomme les acteurs concernés (entreprises, "
    "institutions, dirigeants). Couvre successivement : le fait principal et ses "
    "chiffres clés ; le contexte et l'historique récent ; le détail des données ; "
    "les acteurs et réactions ; les conséquences économiques et de marché ; et ce "
    "qu'il faut surveiller ensuite (catalyseurs, dates). Langage clair et "
    "professionnel. N'invente aucun chiffre qui ne soit pas plausible au vu de "
    "l'extrait ; en cas de doute, reste qualitatif. Neutre et factuel.\n\n"
    "Tu dois aussi fournir une version anglaise du résumé et la traduction du "
    "titre dans les deux langues.\n\n"
    "Enfin, ce site est utilisé par des traders « news / macro » : ajoute une "
    "LECTURE MARCHÉ opérationnelle.\n"
    "- biais : le biais directionnel global pour la prise de risque, avec un ton "
    "parmi 'up' (risk-on / favorable), 'down' (risk-off / défavorable) ou 'flat' "
    "(neutre / dépend des données), et un libellé court FR et EN "
    "(ex. « Risk-on modéré », « Plutôt hawkish », « Neutre »).\n"
    "- impacts : 2 à 4 actifs concrets concernés (indices, devises, taux, "
    "matières premières) avec leur direction probable 'up', 'down' ou 'flat'.\n"
    "- lecture : 1 à 2 phrases d'analyse marché actionnable (FR et EN), sans "
    "conseil d'investissement.\n"
    "- surveiller : le prochain catalyseur / rendez-vous à surveiller (FR et EN).\n"
    "N'invente pas de chiffres précis : laisse l'analyse qualitative.\n\n"
    "Réponds UNIQUEMENT par un objet JSON valide, sans texte autour, de la "
    "forme :\n"
    '{{"titre_fr": "...", "titre_en": "...", '
    '"resume_fr": "par.1\\n\\npar.2\\n\\npar.3", '
    '"resume_en": "p.1\\n\\np.2\\n\\np.3", '
    '"bias": {{"fr": "Risk-on modéré", "en": "Mild risk-on", "tone": "up"}}, '
    '"impacts": [{{"asset": "EUR/USD", "dir": "up"}}, {{"asset": "Bund 10A", "dir": "down"}}], '
    '"market_read": {{"fr": "...", "en": "..."}}, '
    '"watch": {{"fr": "...", "en": "..."}}}}\n\n'
    "Titre : {title}\nExtrait : {excerpt}"
)


def _extract_json(text: str) -> dict | None:
    """Récupère le premier objet JSON présent dans une réponse texte."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except ValueError:
        return None


def summarize_one(title: str, excerpt: str, api_key: str) -> dict | None:
    """Un appel API ; renvoie {titre_fr,titre_en,resume_fr,resume_en} ou None."""
    body = json.dumps({
        "model": MODEL,
        "max_tokens": 2400,
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
        return _extract_json(text)
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
        res = summarize_one(art.get("title", ""), art.get("excerpt", ""), api_key)
        if res and res.get("resume_fr"):
            art["summary"] = res.get("resume_fr", "").strip()
            art["summary_fr"] = res.get("resume_fr", "").strip()
            art["summary_en"] = res.get("resume_en", "").strip()
            art["title_fr"] = res.get("titre_fr", "").strip() or art.get("title")
            art["title_en"] = res.get("titre_en", "").strip() or art.get("title")
            # Lecture marché (pour traders), si fournie par le modèle.
            if isinstance(res.get("bias"), dict):
                art["bias"] = res["bias"]
            if isinstance(res.get("impacts"), list):
                art["impacts"] = res["impacts"]
            if isinstance(res.get("market_read"), dict):
                art["market_read"] = res["market_read"]
            if isinstance(res.get("watch"), dict):
                art["watch"] = res["watch"]
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
