"""Moteur de génération de posts — Python + API Anthropic (§7).

Génère une batch hebdomadaire de posts, déjà différenciés LinkedIn vs X, en
faisant tourner les piliers (§3). Chaque post passe le filtre de conformité
(§6), est sauvegardé localement (toujours), puis poussé dans Notion si la
configuration le permet.

Usage :
    python posts/generate.py                  # 1 batch suivant le plan hebdo
    python posts/generate.py --count 5        # 5 posts
    python posts/generate.py --no-notion      # sans envoyer dans Notion
    python posts/generate.py --dry-run        # n'appelle pas l'API (squelette)
"""

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta

import config
import hooks
from compliance import verifier_post
from prompts import SYSTEM_PROMPT, build_user_prompt


def _client():
    """Initialise le client Anthropic (import paresseux pour le --dry-run)."""
    try:
        from anthropic import Anthropic
    except ImportError:
        sys.exit("Le paquet 'anthropic' est manquant. Lance : pip install -r posts/requirements.txt")
    if not config.ANTHROPIC_API_KEY:
        sys.exit("ANTHROPIC_API_KEY est vide. Voir posts/README.md (création de la clé).")
    return Anthropic(api_key=config.ANTHROPIC_API_KEY)


def generer_un_post(client, pilier_id: str, used_hooks: set) -> dict:
    """Appelle Claude pour un pilier donné et renvoie un dict de post validé."""
    pilier_label = config.PILIERS[pilier_id]
    angle = hooks.pick(hooks.ANGLES_STORYTELLING, used_hooks) if pilier_id == "storytelling" else None
    hook_li = hooks.pick(hooks.HOOKS_LINKEDIN, used_hooks)
    hook_x = hooks.pick(hooks.HOOKS_X, used_hooks)
    user_prompt = build_user_prompt(pilier_id, pilier_label, angle, hook_li, hook_x)

    # `cache_control` sur le prompt système : il est volumineux et identique à
    # chaque post de la batch → on ne le facture quasiment qu'une fois.
    resp = client.messages.create(
        model=config.MODEL,
        max_tokens=2000,
        system=[{
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": user_prompt}],
    )
    brut = resp.content[0].text.strip()
    post = _parse_json(brut)
    post["pilier_label"] = pilier_label
    return verifier_post(post)


def _parse_json(brut: str) -> dict:
    """Extrait l'objet JSON même si le modèle l'entoure d'un bloc ```json."""
    s = brut.strip()
    if s.startswith("```"):
        s = s.split("```", 2)[1]
        if s.startswith("json"):
            s = s[4:]
    s = s.strip().strip("`").strip()
    return json.loads(s)


def _squelette(pilier_id: str) -> dict:
    """Post factice pour --dry-run (teste le pipeline sans appeler l'API)."""
    return verifier_post({
        "idee": f"[dry-run] idée pour {pilier_id}",
        "pilier": pilier_id,
        "pilier_label": config.PILIERS[pilier_id],
        "parle_de_trading": False,
        "pousse_vers_broker": False,
        "linkedin": {"texte": "[dry-run] post LinkedIn.", "hashtags": ["#leterminal"]},
        "x": {"thread": ["[dry-run] tweet 1"], "hashtags": []},
    })


def sauver_local(posts: list, semaine: str) -> str:
    """Écrit la batch en JSON + en Markdown lisible. Renvoie le chemin Markdown."""
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    base = os.path.join(config.OUTPUT_DIR, f"batch_{semaine}")

    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    md = [f"# Batch éditoriale — semaine {semaine}\n"]
    for i, p in enumerate(posts, 1):
        c = p["conformite"]["statut"]
        badge = {"OK": "✅", "WARN": "⚠️", "BLOCK": "⛔"}[c]
        md.append(f"\n## {i}. {badge} {p['pilier_label']} — conformité : {c}")
        md.append(f"\n*Idée : {p['idee']}*\n")
        if c != "OK":
            for plat in ("linkedin", "x"):
                for r in p["conformite"][plat]["raisons"]:
                    md.append(f"> {plat} : {r}")
        md.append("\n### LinkedIn\n")
        md.append(p["linkedin"]["texte"])
        md.append("\n" + " ".join(p["linkedin"].get("hashtags", [])))
        md.append("\n### X (thread)\n")
        for j, t in enumerate(p["x"]["thread"], 1):
            md.append(f"{j}. {t}")
        if p["x"].get("hashtags"):
            md.append(" ".join(p["x"]["hashtags"]))
        md.append("\n---")

    with open(base + ".md", "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    return base + ".md"


def main():
    ap = argparse.ArgumentParser(description="Génère une batch de posts Le Terminal.")
    ap.add_argument("--count", type=int, default=len(config.PLAN_HEBDO),
                    help="Nombre de posts à générer (défaut : plan hebdo).")
    ap.add_argument("--no-notion", action="store_true", help="Ne pas pousser dans Notion.")
    ap.add_argument("--dry-run", action="store_true", help="Ne pas appeler l'API (test pipeline).")
    args = ap.parse_args()

    # Semaine ISO courante comme identifiant de batch (ex. 2026-W23).
    today = date.today()
    semaine = f"{today.isocalendar().year}-W{today.isocalendar().week:02d}"

    # Construit la liste des piliers (boucle sur le plan si count > plan).
    plan = [config.PLAN_HEBDO[i % len(config.PLAN_HEBDO)] for i in range(args.count)]

    client = None if args.dry_run else _client()
    used_hooks, posts = set(), []
    for n, pilier_id in enumerate(plan, 1):
        print(f"  ({n}/{len(plan)}) génération — pilier : {pilier_id} …")
        try:
            post = _squelette(pilier_id) if args.dry_run else generer_un_post(client, pilier_id, used_hooks)
        except Exception as e:  # on n'interrompt pas toute la batch pour un post
            print(f"      ⚠️ échec : {e}")
            continue
        # Propose une date de publication étalée (1 post/jour à partir de demain).
        post["date_prevue"] = (today + timedelta(days=n)).isoformat()
        posts.append(post)

    chemin = sauver_local(posts, semaine)
    nb_block = sum(1 for p in posts if p["conformite"]["statut"] == "BLOCK")
    print(f"\n✅ {len(posts)} posts générés → {chemin}")
    if nb_block:
        print(f"⛔ {nb_block} post(s) BLOQUÉ(S) par la conformité : à corriger avant publication.")

    # Couche Notion (optionnelle).
    if not args.no_notion and config.NOTION_TOKEN and config.NOTION_DATABASE_ID:
        try:
            from notion_sync import pousser_batch
            pousser_batch(posts, semaine)
            print("📋 Posts envoyés dans Notion (statut : Brouillon).")
        except Exception as e:
            print(f"⚠️ Envoi Notion échoué : {e}")
    elif not args.no_notion:
        print("ℹ️ Notion non configuré (NOTION_TOKEN / NOTION_DATABASE_ID) — sortie locale seulement.")


if __name__ == "__main__":
    main()
