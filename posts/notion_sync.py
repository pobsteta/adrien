"""Envoi des posts générés dans la base Notion « Calendrier éditorial » (§4.2).

Une page Notion = une version de post (LinkedIn OU X), pour pouvoir programmer
chaque plateforme indépendamment dans Publer. Le contenu rédigé va dans le CORPS
de la page ; les métadonnées (statut, plateforme, pilier, date, conformité) vont
dans les propriétés.

Statut initial : « Brouillon » → c'est TOI qui passes en « Validé » après revue
humaine (obligatoire, §0.4 / §6).

Nécessite : pip install notion-client, + NOTION_TOKEN et NOTION_DATABASE_ID.
"""

import config

# Correspondance verdict conformité interne → libellé Notion
_CONF = {"OK": "OK", "WARN": "À revoir", "BLOCK": "Bloqué"}


def _client():
    from notion_client import Client
    if not (config.NOTION_TOKEN and config.NOTION_DATABASE_ID):
        raise RuntimeError("NOTION_TOKEN / NOTION_DATABASE_ID manquants.")
    return Client(auth=config.NOTION_TOKEN)


def _blocs_texte(texte: str) -> list:
    """Découpe un texte en blocs paragraphe Notion (limite ~2000 car./bloc)."""
    blocs = []
    for para in texte.split("\n"):
        morceaux = [para[i:i + 1900] for i in range(0, len(para), 1900)] or [""]
        for m in morceaux:
            blocs.append({
                "object": "block", "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": m}}]},
            })
    return blocs


def _page(notion, post: dict, plateforme: str, semaine: str):
    cle = plateforme.lower()  # "linkedin" ou "x"
    conf_statut = _CONF[post["conformite"][cle]["statut"]]

    if plateforme == "LinkedIn":
        texte = post["linkedin"]["texte"] + "\n\n" + " ".join(post["linkedin"].get("hashtags", []))
    else:  # X
        thread = post["x"]["thread"]
        texte = "\n\n".join(f"{i}/ {t}" for i, t in enumerate(thread, 1))
        if post["x"].get("hashtags"):
            texte += "\n\n" + " ".join(post["x"]["hashtags"])

    props = {
        "Titre": {"title": [{"text": {"content": f"{post['idee'][:90]} — {plateforme}"}}]},
        "Plateforme": {"select": {"name": plateforme}},
        "Pilier": {"select": {"name": post["pilier_label"]}},
        "Statut": {"select": {"name": "Brouillon"}},
        "Conformité": {"select": {"name": conf_statut}},
        "Semaine": {"rich_text": [{"text": {"content": semaine}}]},
    }
    if post.get("date_prevue"):
        props["Date prévue"] = {"date": {"start": post["date_prevue"]}}

    notion.pages.create(
        parent={"database_id": config.NOTION_DATABASE_ID},
        properties=props,
        children=_blocs_texte(texte),
    )


def pousser_batch(posts: list, semaine: str) -> None:
    """Crée 2 pages Notion par post (LinkedIn + X)."""
    notion = _client()
    for post in posts:
        _page(notion, post, "LinkedIn", semaine)
        _page(notion, post, "X", semaine)
