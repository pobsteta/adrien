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

import hashlib
import json
import re
import shutil
import sys
import unicodedata
from datetime import datetime, timezone, date, timedelta
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
FEEDS_PATH = ROOT / "sources" / "feeds.json"

SELECTION_LABEL = "La sélection"

# Section « Flash » : les annonces les plus récentes, tous flux confondus.
FLASH_LABEL = "Flash"
FLASH_COUNT = 6              # nombre d'annonces dans le fil Flash
FLASH_MAX_AGE_HOURS = 12     # une annonce n'est « flash » que si récente

# Ordre d'affichage des rubriques ; les continents d'abord, puis les
# institutions et l'international. Les rubriques absentes de cette liste sont
# placées ensuite, par poids décroissant puis ordre alpha.
CATEGORY_ORDER = [
    "Europe", "Amériques", "Asie", "Afrique", "Océanie",
    "Marchés", "Institutions", "International",
]

# Icône de menu propre à chaque rubrique (thème finance), repli sur « globe ».
CATEGORY_ICONS = {
    "Europe": "euro", "Amériques": "dollar", "Asie": "yen",
    "Afrique": "sun", "Océanie": "waves", "Marchés": "chart",
    "Institutions": "bank", "International": "globe", "France": "hexagon",
    "Crypto": "crypto",
}

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


def count_sources() -> int:
    """Nombre de sources RSS configurées (pour la présentation)."""
    if not FEEDS_PATH.exists():
        return 0
    with FEEDS_PATH.open(encoding="utf-8") as fh:
        return len(json.load(fh))


# --------------------------------------------------------------------------- #
# Préparation pour l'affichage                                                  #
# --------------------------------------------------------------------------- #
def resolve_summary(article: dict) -> str:
    """Texte à afficher : le résumé (IA) sinon l'extrait du flux."""
    return (article.get("summary") or article.get("excerpt") or "").strip()


def article_id(article: dict) -> str:
    """Identifiant stable d'une annonce (pour sa page dédiée)."""
    if article.get("id"):
        return article["id"]
    basis = (article.get("url") or article.get("title") or "").strip().lower()
    return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]


def summary_kind(article: dict, manual: bool = False) -> str:
    """Origine du texte affiché : 'edito' (rédaction), 'ai' (résumé IA) ou
    'excerpt' (extrait brut du flux). Pilote la mention sur la page dédiée."""
    if manual:
        return "edito"
    return "ai" if (article.get("summary") or "").strip() else "excerpt"


def time_display(published: str | None) -> str:
    """ISO -> « 08:12 » (heure locale du serveur), vide si pas de date."""
    if not published:
        return ""
    dt = datetime.fromisoformat(published).astimezone()
    return dt.strftime("%H:%M")


# Catégorie dédiée à sa propre page (hors flux d'actualité générale).
CRYPTO_LABEL = "Crypto"


def freshness_key(article: dict):
    """Date de publication pour trier du plus récent au plus ancien.

    Les annonces sans date passent en dernier. Toujours « aware » (UTC) pour
    permettre la comparaison.
    """
    published = article.get("published")
    if published:
        return datetime.fromisoformat(published)
    return datetime.min.replace(tzinfo=timezone.utc)


def paragraphs(text: str) -> list[str]:
    """Découpe un texte en paragraphes (sur sauts de ligne), liste non vide."""
    parts = [p.strip() for p in re.split(r"\n+", text or "") if p.strip()]
    return parts


def short_teaser(text: str, limit: int = 90) -> str:
    """Accroche courte pour l'accueil : une ligne tronquée proprement.

    Le résumé complet, lui, reste sur la page dédiée de l'annonce.
    """
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:.—-")
    return f"{cut}…"


def prepare_article(article: dict) -> dict:
    """Enrichit un article agrégé des champs d'affichage (FR + EN)."""
    aid = article_id(article)
    excerpt = (article.get("excerpt") or "").strip()
    full_fr = (article.get("summary_fr") or article.get("summary") or excerpt).strip()
    full_en = (article.get("summary_en") or article.get("summary")
               or article.get("excerpt_en") or excerpt).strip()
    excerpt_en = (article.get("excerpt_en") or excerpt).strip()
    return {
        **article,
        "id": aid,
        "page_name": f"{aid}.html",
        "image": (article.get("image") or "").strip(),
        "title_fr": article.get("title_fr") or article.get("title", ""),
        "title_en": article.get("title_en") or article.get("title", ""),
        # Accroche COURTE pour l'accueil ; le détail complet est sur la page dédiée.
        "display_summary": short_teaser(excerpt or full_fr),
        "display_summary_en": short_teaser(excerpt_en or full_en),
        "summary_fr_paras": paragraphs(full_fr),
        "summary_en_paras": paragraphs(full_en),
        "summary_kind": summary_kind(article),
        "time_display": time_display(article.get("published")),
    }


def prepare_manual(item: dict) -> dict:
    """Adapte un item de la sélection manuelle au schéma d'affichage (FR + EN)."""
    aid = article_id(item)
    full_fr = (item.get("summary") or item.get("summary_fr") or "").strip()
    full_en = (item.get("summary_en") or full_fr).strip()
    return {
        "id": aid,
        "page_name": f"{aid}.html",
        "title": item.get("title", ""),
        "title_fr": item.get("title_fr") or item.get("title", ""),
        "title_en": item.get("title_en") or item.get("title", ""),
        "url": item.get("url", ""),
        "source": item.get("source", ""),
        "category": SELECTION_LABEL,
        "image": (item.get("image") or "").strip(),
        # Accroche COURTE pour l'accueil ; le détail complet est sur la page dédiée.
        "display_summary": short_teaser(full_fr),
        "display_summary_en": short_teaser(item.get("excerpt_en") or full_en),
        "summary_fr_paras": paragraphs(full_fr),
        "summary_en_paras": paragraphs(full_en),
        "summary_kind": "edito",
        "time_display": "",
        # Champs « Lecture marché » (pour traders), optionnels.
        "bias": item.get("bias"),
        "impacts": item.get("impacts"),
        "market_read": item.get("market_read"),
        "watch": item.get("watch"),
        "data_points": item.get("data_points"),
    }


def slugify(text: str) -> str:
    """« Amériques » -> « ameriques » : ancre HTML stable et sûre."""
    norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    norm = re.sub(r"[^a-zA-Z0-9]+", "-", norm).strip("-").lower()
    return norm or "rubrique"


def group_by_category(articles: list[dict]) -> list[dict]:
    """Regroupe les articles agrégés en rubriques ordonnées (avec ancre)."""
    buckets: dict[str, list[dict]] = {}
    for art in articles:
        buckets.setdefault(art["category"], []).append(art)

    def sort_key(category: str) -> tuple:
        if category in CATEGORY_ORDER:
            return (0, CATEGORY_ORDER.index(category), category)
        max_weight = max(a["weight"] for a in buckets[category])
        return (1, -max_weight, category)

    return [
        {"category": cat, "anchor": "r-" + slugify(cat),
         "icon": CATEGORY_ICONS.get(cat, "globe"),
         "articles": sorted(buckets[cat], key=freshness_key, reverse=True)}
        for cat in sorted(buckets, key=sort_key)
    ]


# --------------------------------------------------------------------------- #
# Construction du contexte de rendu                                            #
# --------------------------------------------------------------------------- #
def build_context(edition_date: str) -> dict:
    aggregated = [prepare_article(a) for a in load_aggregated()]
    selection = [prepare_manual(m) for m in load_manual(edition_date)]

    # Tri par fraîcheur (plus récent d'abord), appliqué à tout l'agrégat.
    aggregated.sort(key=freshness_key, reverse=True)

    # La crypto a sa page dédiée : on la sort du flux d'actualité générale.
    crypto = [a for a in aggregated if a.get("category") == CRYPTO_LABEL]
    mainstream = [a for a in aggregated if a.get("category") != CRYPTO_LABEL]

    # L'article « à la une » : la plus fraîche des annonces générales. On la
    # retire de sa rubrique pour éviter le doublon.
    featured = mainstream[0] if mainstream else None
    rest = mainstream[1:] if mainstream else []
    sections = group_by_category(rest)

    # Fil « Flash » : les annonces les plus récentes (hors une), tous flux
    # confondus, limitées aux plus fraîches. C'est un digest transversal :
    # ses annonces peuvent réapparaître dans leur rubrique géographique.
    flash = build_flash(rest)

    # Bandeau défilant (effet « terminal ») : un condensé source · titre.
    ticker = [
        {"label": a["source"], "title": a["title"]}
        for a in (selection + aggregated)
    ]

    # Menu déroulant : toutes les sections réellement présentes, dans l'ordre
    # d'apparition. `anchor` = id HTML vers lequel le lien saute.
    menu: list[dict] = []
    if featured:
        menu.append({"label": "À la une", "anchor": "une",
                     "icon": "star", "group": "edition"})
    if flash:
        menu.append({"label": "Flash", "anchor": "flash",
                     "icon": "bolt", "group": "edition"})
    if selection:
        menu.append({"label": "La sélection", "anchor": "selection",
                     "icon": "bookmark", "group": "edition"})
    menu += [{"label": s["category"], "anchor": s["anchor"],
              "icon": CATEGORY_ICONS.get(s["category"], "globe"),
              "group": "zone", "count": len(s["articles"])} for s in sections]

    d = date.fromisoformat(edition_date)
    return {
        "edition_date": edition_date,
        "edition_date_human": human_date(d),
        "generated_at_human": datetime.now().strftime("%d/%m/%Y à %H:%M"),
        "selection": selection,
        "featured": featured,
        "flash": flash,
        "sections": sections,
        "crypto": crypto,
        "ticker": ticker,
        "menu": menu,
        "total_count": len(aggregated) + len(selection),
        # Chiffres pour le bandeau de présentation (première page).
        "stats": {
            "sources": count_sources(),
            "zones": len(sections),
            "annonces": len(aggregated) + len(selection),
        },
    }


def _published_key(article: dict) -> datetime:
    """Clé de fraîcheur pour un article préparé (sans date -> très ancien)."""
    if article.get("published"):
        return datetime.fromisoformat(article["published"])
    return datetime.min.replace(tzinfo=timezone.utc)


def build_flash(articles: list[dict]) -> list[dict]:
    """Sélectionne les annonces les plus récentes pour le fil Flash."""
    now = datetime.now(timezone.utc)
    horizon = now - timedelta(hours=FLASH_MAX_AGE_HOURS)
    fresh = [a for a in articles
             if a.get("published") and _published_key(a) >= horizon]
    fresh.sort(key=_published_key, reverse=True)
    return fresh[:FLASH_COUNT]


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

    # Ressources statiques copiées à la racine du site.
    shutil.copyfile(TEMPLATES_DIR / "style.css", OUTPUT_DIR / "style.css")
    shutil.copyfile(TEMPLATES_DIR / "app.js", OUTPUT_DIR / "app.js")

    env = make_env()
    context = build_context(edition_date)
    print(f"  sélection : {len(context['selection'])} · "
          f"agrégés : {context['total_count'] - len(context['selection'])} · "
          f"à la une : {'oui' if context['featured'] else 'non'}")

    edition_tpl = env.get_template("edition.html")

    # 1) Édition du jour : output/index.html (ressources à la racine).
    (OUTPUT_DIR / "index.html").write_text(
        edition_tpl.render(css_path="style.css",
                           js_path="app.js",
                           archives_path="archives/index.html",
                           anchor_base="",
                           annonces_base="annonces/",
                           is_archive=False,
                           **context),
        encoding="utf-8",
    )
    print("  écrit : output/index.html")

    # 2) Copie archivée : output/archives/AAAA-MM-JJ.html (ressources au-dessus).
    archive_file = ARCHIVES_DIR / f"{edition_date}.html"
    archive_file.write_text(
        edition_tpl.render(css_path="../style.css",
                           js_path="../app.js",
                           archives_path="index.html",
                           anchor_base="",
                           annonces_base="../annonces/",
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
                            js_path="../app.js",
                            home_path="../index.html",
                            archives=archives,
                            menu=context["menu"]),
        encoding="utf-8",
    )
    print(f"  écrit : output/archives/index.html ({len(archives)} édition(s))")

    # 4) Page « À propos » (présentation détaillée du site).
    about_tpl = env.get_template("apropos.html")
    (OUTPUT_DIR / "a-propos.html").write_text(
        about_tpl.render(css_path="style.css",
                         js_path="app.js",
                         **context),
        encoding="utf-8",
    )
    print("  écrit : output/a-propos.html")

    # 5) Page « Calendrier économique » (widget Investing.com, 3 étoiles).
    cal_tpl = env.get_template("calendrier.html")
    (OUTPUT_DIR / "calendrier.html").write_text(
        cal_tpl.render(css_path="style.css",
                       js_path="app.js",
                       **context),
        encoding="utf-8",
    )
    print("  écrit : output/calendrier.html")

    # 6) Page dédiée « Crypto » (ticker crypto + grille d'annonces).
    crypto_tpl = env.get_template("crypto.html")
    (OUTPUT_DIR / "crypto.html").write_text(
        crypto_tpl.render(css_path="style.css",
                          js_path="app.js",
                          annonces_base="annonces/",
                          **context),
        encoding="utf-8",
    )
    print(f"  écrit : output/crypto.html ({len(context['crypto'])} annonce(s))")

    # 7) Une page dédiée par annonce (résumé + image + lien source).
    annonces_dir = OUTPUT_DIR / "annonces"
    annonces_dir.mkdir(parents=True, exist_ok=True)
    annonce_tpl = env.get_template("annonce.html")

    pool: dict[str, dict] = {}
    if context["featured"]:
        pool[context["featured"]["id"]] = context["featured"]
    for section in context["sections"]:
        for art in section["articles"]:
            pool[art["id"]] = art
    for art in context["crypto"]:
        pool[art["id"]] = art
    for art in context["selection"]:
        pool.setdefault(art["id"], art)

    for art in pool.values():
        (annonces_dir / art["page_name"]).write_text(
            annonce_tpl.render(css_path="../style.css",
                               js_path="../app.js",
                               home_path="../index.html",
                               anchor_base="../index.html",
                               annonces_base="",
                               art=art,
                               menu=context["menu"]),
            encoding="utf-8",
        )
    print(f"  écrit : output/annonces/ ({len(pool)} page(s) d'annonce)")

    print("Terminé.")
    return 0


def main() -> int:
    edition_date = sys.argv[1] if len(sys.argv) > 1 else None
    return build(edition_date)


if __name__ == "__main__":
    sys.exit(main())
