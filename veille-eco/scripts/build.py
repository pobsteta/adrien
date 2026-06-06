#!/usr/bin/env python3
"""Génération du site statique « La Quotidienne Éco ».

Assemble la sélection manuelle (``data/manual.json``) et les articles agrégés
(``data/aggregated.json``), regroupe par rubrique, désigne un article « à la
une », rend les gabarits Jinja2 et écrit :

  - ``output/index.html``                  : l'édition du jour
  - ``output/archives/AAAA-MM-JJ.html``    : la copie archivée
  - ``output/archives/index.html``         : l'index des archives
  - ``output/style.css``                   : la feuille de style (copiée)

Aucune base de données, aucun appel réseau ici : on ne fait qu'assembler des
fichiers JSON locaux. L'étape de résumé (IA) viendra plus tard, entre
``aggregate.py`` et ``build.py``, en remplissant le champ ``summary`` ; tant
qu'il est vide, l'affichage retombe sur ``excerpt`` (voir ``resolve_summary``).
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone, date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

# --------------------------------------------------------------------------- #
# Chemins                                                                      #
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / "templates"
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"
ARCHIVES_DIR = OUTPUT_DIR / "archives"

AGGREGATED_PATH = DATA_DIR / "aggregated.json"
MANUAL_PATH = DATA_DIR / "manual.json"

SELECTION_LABEL = "La sélection"

# Ordre d'affichage des rubriques agrégées ; les rubriques absentes de cette
# liste sont placées ensuite, par poids décroissant puis ordre alphabétique.
CATEGORY_ORDER = ["France", "Institutions", "International"]

# --------------------------------------------------------------------------- #
# Dates en français (sans dépendre de la locale système)                      #
# --------------------------------------------------------------------------- #
_FR_DAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi",
            "dimanche"]
_FR_MONTHS = ["", "janvier", "février", "mars", "avril", "mai", "juin",
              "juillet", "août", "septembre", "octobre", "novembre",
              "décembre"]


def human_date(d: date) -> str:
    """2026-06-06 -> « vendredi 6 juin 2026 »."""
    return f"{_FR_DAYS[d.weekday()]} {d.day} {_FR_MONTHS[d.month]} {d.year}"


# --------------------------------------------------------------------------- #
# Chargement des données                                                        #
# --------------------------------------------------------------------------- #
def load_aggregated() -> list[dict]:
    if not AGGREGATED_PATH.exists():
        print(f"  (aucun {AGGREGATED_PATH.name}, on continue sans agrégat)")
        return []
    with AGGREGATED_PATH.open(encoding="utf-8") as fh:
        return json.load(fh).get("articles", [])


def load_manual(edition_date: str) -> list[dict]:
    """Charge la sélection manuelle, filtrée sur la date d'édition."""
    if not MANUAL_PATH.exists():
        return []
    with MANUAL_PATH.open(encoding="utf-8") as fh:
        items = json.load(fh)
    return [it for it in items if it.get("date") == edition_date]


# --------------------------------------------------------------------------- #
# Préparation pour l'affichage                                                  #
# --------------------------------------------------------------------------- #
def resolve_summary(article: dict) -> str:
    """Texte à afficher : le résumé (futur, IA) sinon l'extrait du flux."""
    return (article.get("summary") or article.get("excerpt") or "").strip()


def time_display(published: str | None) -> str:
    """ISO -> « 08:12 » (heure locale du serveur), vide si pas de date."""
    if not published:
        return ""
    dt = datetime.fromisoformat(published).astimezone()
    return dt.strftime("%H:%M")


def prepare_article(article: dict) -> dict:
    """Enrichit un article agrégé des champs d'affichage."""
    return {
        **article,
        "display_summary": resolve_summary(article),
        "time_display": time_display(article.get("published")),
    }


def prepare_manual(item: dict) -> dict:
    """Adapte un item de la sélection manuelle au schéma d'affichage."""
    return {
        "title": item.get("title", ""),
        "url": item.get("url", ""),
        "source": item.get("source", ""),
        "category": SELECTION_LABEL,
        "display_summary": (item.get("summary") or "").strip(),
        "time_display": "",
    }


def group_by_category(articles: list[dict]) -> list[dict]:
    """Regroupe les articles agrégés en rubriques ordonnées."""
    buckets: dict[str, list[dict]] = {}
    for art in articles:
        buckets.setdefault(art["category"], []).append(art)

    def sort_key(category: str) -> tuple:
        if category in CATEGORY_ORDER:
            return (0, CATEGORY_ORDER.index(category), category)
        max_weight = max(a["weight"] for a in buckets[category])
        return (1, -max_weight, category)

    return [
        {"category": cat, "articles": buckets[cat]}
        for cat in sorted(buckets, key=sort_key)
    ]


# --------------------------------------------------------------------------- #
# Construction du contexte de rendu                                            #
# --------------------------------------------------------------------------- #
def build_context(edition_date: str) -> dict:
    aggregated = [prepare_article(a) for a in load_aggregated()]
    selection = [prepare_manual(m) for m in load_manual(edition_date)]

    # L'article « à la une » : le mieux classé des agrégés (déjà trié par
    # poids puis fraîcheur dans aggregate.py). On le retire de sa rubrique
    # pour éviter le doublon.
    featured = aggregated[0] if aggregated else None
    rest = aggregated[1:] if aggregated else []
    sections = group_by_category(rest)

    # Bandeau défilant (effet « terminal ») : un condensé source · titre.
    ticker = [
        {"label": a["source"], "title": a["title"]}
        for a in (selection + aggregated)
    ]

    d = date.fromisoformat(edition_date)
    return {
        "edition_date": edition_date,
        "edition_date_human": human_date(d),
        "generated_at_human": datetime.now().strftime("%d/%m/%Y à %H:%M"),
        "selection": selection,
        "featured": featured,
        "sections": sections,
        "ticker": ticker,
        "total_count": len(aggregated) + len(selection),
    }


# --------------------------------------------------------------------------- #
# Archives                                                                      #
# --------------------------------------------------------------------------- #
def list_archives() -> list[dict]:
    """Scanne output/archives/*.html pour bâtir l'index (récent d'abord)."""
    entries = []
    for path in sorted(ARCHIVES_DIR.glob("*.html"), reverse=True):
        if path.stem == "index":
            continue
        try:
            d = date.fromisoformat(path.stem)
        except ValueError:
            continue
        entries.append({
            "date": path.stem,
            "human": human_date(d),
            "href": f"{path.stem}.html",
        })
    return entries


# --------------------------------------------------------------------------- #
# Rendu                                                                         #
# --------------------------------------------------------------------------- #
def make_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def build(edition_date: str | None = None) -> int:
    edition_date = edition_date or date.today().isoformat()
    print(f"Génération de l'édition du {edition_date} :")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVES_DIR.mkdir(parents=True, exist_ok=True)

    # Feuille de style copiée à la racine du site.
    shutil.copyfile(TEMPLATES_DIR / "style.css", OUTPUT_DIR / "style.css")

    env = make_env()
    context = build_context(edition_date)
    print(f"  sélection : {len(context['selection'])} · "
          f"agrégés : {context['total_count'] - len(context['selection'])} · "
          f"à la une : {'oui' if context['featured'] else 'non'}")

    edition_tpl = env.get_template("edition.html")

    # 1) Édition du jour : output/index.html (css à la racine).
    (OUTPUT_DIR / "index.html").write_text(
        edition_tpl.render(css_path="style.css",
                           archives_path="archives/index.html",
                           is_archive=False,
                           **context),
        encoding="utf-8",
    )
    print("  écrit : output/index.html")

    # 2) Copie archivée : output/archives/AAAA-MM-JJ.html (css un cran au-dessus).
    archive_file = ARCHIVES_DIR / f"{edition_date}.html"
    archive_file.write_text(
        edition_tpl.render(css_path="../style.css",
                           archives_path="index.html",
                           is_archive=True,
                           **context),
        encoding="utf-8",
    )
    print(f"  écrit : output/archives/{edition_date}.html")

    # 3) Index des archives (après écriture, pour inclure l'édition du jour).
    archives = list_archives()
    archives_tpl = env.get_template("archives.html")
    (ARCHIVES_DIR / "index.html").write_text(
        archives_tpl.render(css_path="../style.css",
                            home_path="../index.html",
                            archives=archives),
        encoding="utf-8",
    )
    print(f"  écrit : output/archives/index.html ({len(archives)} édition(s))")

    print("Terminé.")
    return 0


def main() -> int:
    edition_date = sys.argv[1] if len(sys.argv) > 1 else None
    return build(edition_date)


if __name__ == "__main__":
    sys.exit(main())
