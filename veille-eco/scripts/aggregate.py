#!/usr/bin/env python3
"""Agrégation des flux RSS pour « La Quotidienne Éco ».

Lit les sources décrites dans ``sources/feeds.json``, télécharge chaque flux,
normalise les articles dans un schéma commun, déduplique, ne garde que les
articles récents, plafonne le volume puis trie. Le résultat est écrit dans
``data/aggregated.json``.

Schéma d'un article normalisé (ce qui circule vers ``build.py``) ::

    {
      "id":        "hash de déduplication",
      "title":     "Titre de l'article",
      "url":       "https://...",
      "source":    "Le Monde – Économie",
      "category":  "France",
      "weight":    4,
      "published": "2026-06-06T08:12:00+00:00",  # ISO 8601, UTC
      "excerpt":   "extrait nettoyé fourni par le flux",
      "summary":   null   # réservé à une future étape de résumé (IA)
    }

Note droit d'auteur : on ne stocke que titre + court extrait + lien retour,
jamais l'article complet, et la source est toujours créditée.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

import feedparser

# --------------------------------------------------------------------------- #
# Réglages (seuils en constantes, faciles à ajuster)                          #
# --------------------------------------------------------------------------- #
LOOKBACK_HOURS = 36          # fenêtre de fraîcheur : on ignore le plus ancien
MAX_PER_SOURCE = 8           # plafond d'articles conservés par source
MAX_TOTAL = 60               # plafond global d'articles dans l'édition
EXCERPT_MAX_CHARS = 280      # longueur max de l'extrait (résumé de secours)
REQUEST_TIMEOUT = 15         # secondes avant d'abandonner un flux injoignable

# Paramètres d'URL à supprimer pour fiabiliser la déduplication.
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "xtor", "ref", "fbclid", "gclid", "at_medium", "at_campaign",
}

# --------------------------------------------------------------------------- #
# Chemins                                                                      #
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parent.parent
FEEDS_PATH = ROOT / "sources" / "feeds.json"
OUTPUT_PATH = ROOT / "data" / "aggregated.json"


# --------------------------------------------------------------------------- #
# Nettoyage / normalisation                                                    #
# --------------------------------------------------------------------------- #
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def clean_text(raw: str) -> str:
    """Retire le HTML et normalise les espaces d'un extrait de flux."""
    if not raw:
        return ""
    text = _TAG_RE.sub(" ", raw)      # supprime les balises
    text = html.unescape(text)        # &eacute; -> é, &amp; -> & ...
    text = _WS_RE.sub(" ", text)      # espaces multiples -> simple
    return text.strip()


def shorten(text: str, limit: int = EXCERPT_MAX_CHARS) -> str:
    """Tronque proprement sur une frontière de mot, suffixe « … »."""
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",;:.")
    return f"{cut}…"


def canonical_url(url: str) -> str:
    """Normalise une URL (retire le tracking) pour la déduplication."""
    if not url:
        return ""
    parts = urlsplit(url.strip())
    query = [(k, v) for k, v in parse_qsl(parts.query)
             if k.lower() not in TRACKING_PARAMS]
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme, netloc, path, urlencode(query), ""))


def make_id(url: str, title: str) -> str:
    """Identifiant stable de déduplication (URL canonique sinon titre)."""
    basis = canonical_url(url) or title.lower().strip()
    return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]


def parse_date(entry) -> datetime | None:
    """Extrait une date timezone-aware (UTC) d'une entrée feedparser."""
    for attr in ("published_parsed", "updated_parsed"):
        struct = getattr(entry, attr, None)
        if struct:
            # struct_time est en UTC pour les champs *_parsed de feedparser.
            return datetime(*struct[:6], tzinfo=timezone.utc)
    return None


def best_excerpt(entry) -> str:
    """Choisit le meilleur champ de résumé fourni par le flux."""
    raw = ""
    if getattr(entry, "summary", ""):
        raw = entry.summary
    elif getattr(entry, "content", None):
        raw = entry.content[0].get("value", "")
    elif getattr(entry, "description", ""):
        raw = entry.description
    return shorten(clean_text(raw))


# --------------------------------------------------------------------------- #
# Cœur de l'agrégation                                                         #
# --------------------------------------------------------------------------- #
def load_feeds() -> list[dict]:
    with FEEDS_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def normalize_entry(entry, source: dict) -> dict | None:
    """Transforme une entrée brute en article normalisé, ou None si invalide."""
    title = clean_text(getattr(entry, "title", ""))
    url = getattr(entry, "link", "")
    if not title or not url:
        return None

    published = parse_date(entry)
    return {
        "id": make_id(url, title),
        "title": title,
        "url": url,
        "source": source["name"],
        "category": source.get("category", "Divers"),
        "weight": int(source.get("weight", 1)),
        "published": published.isoformat() if published else None,
        "excerpt": best_excerpt(entry),
        # Champ distinct, réservé à une future étape de résumé (IA).
        # Tant qu'il vaut None, l'affichage retombe sur `excerpt`.
        "summary": None,
    }


def fetch_source(source: dict, now: datetime) -> list[dict]:
    """Télécharge et normalise un flux ; renvoie ses articles frais."""
    url = source["url"]
    print(f"  → {source['name']}: ", end="", flush=True)
    try:
        parsed = feedparser.parse(url, request_headers={
            "User-Agent": "QuotidienneEco/1.0 (+veille presse éco)"
        })
    except Exception as exc:  # réseau, parsing... on isole la panne d'un flux
        print(f"échec ({exc})")
        return []

    if getattr(parsed, "bozo", False) and not parsed.entries:
        print(f"injoignable/illisible ({getattr(parsed, 'bozo_exception', '?')})")
        return []

    horizon = now - timedelta(hours=LOOKBACK_HOURS)
    articles: list[dict] = []
    for entry in parsed.entries:
        art = normalize_entry(entry, source)
        if art is None:
            continue
        # Filtre de fraîcheur : on garde les articles sans date (prudence),
        # on écarte ceux clairement trop anciens.
        if art["published"]:
            published = datetime.fromisoformat(art["published"])
            if published < horizon:
                continue
        articles.append(art)

    # Plafond par source (les plus récents d'abord).
    articles.sort(key=_freshness_key, reverse=True)
    kept = articles[:MAX_PER_SOURCE]
    print(f"{len(kept)} article(s)")
    return kept


def _freshness_key(article: dict) -> datetime:
    """Clé de fraîcheur ; les articles sans date passent en dernier."""
    if article["published"]:
        return datetime.fromisoformat(article["published"])
    return datetime.min.replace(tzinfo=timezone.utc)


def deduplicate(articles: list[dict]) -> list[dict]:
    """Supprime les doublons inter-sources, en gardant le plus pondéré."""
    by_id: dict[str, dict] = {}
    for art in articles:
        existing = by_id.get(art["id"])
        if existing is None or art["weight"] > existing["weight"]:
            by_id[art["id"]] = art
    return list(by_id.values())


def aggregate() -> list[dict]:
    now = datetime.now(timezone.utc)
    feeds = load_feeds()
    print(f"Agrégation de {len(feeds)} source(s) "
          f"(fenêtre {LOOKBACK_HOURS} h) :")

    collected: list[dict] = []
    for source in feeds:
        collected.extend(fetch_source(source, now))

    collected = deduplicate(collected)

    # Tri final : poids décroissant, puis fraîcheur décroissante.
    collected.sort(key=lambda a: (a["weight"], _freshness_key(a)), reverse=True)

    collected = collected[:MAX_TOTAL]
    print(f"Total retenu : {len(collected)} article(s) "
          f"(plafond {MAX_TOTAL}).")
    return collected


def main() -> int:
    articles = aggregate()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(articles),
        "articles": articles,
    }
    with OUTPUT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print(f"Écrit : {OUTPUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
