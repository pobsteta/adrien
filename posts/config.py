"""Configuration du moteur de génération de posts « Le Terminal ».

Toutes les valeurs sensibles (clés API, IDs) sont lues depuis des variables
d'environnement pour ne JAMAIS être commitées. Voir `.env.example`.
"""

import os

# --- Clé API Anthropic (obligatoire pour générer) -------------------------
# À créer sur https://console.anthropic.com → Settings → API Keys
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Modèle Claude utilisé pour la rédaction.
#   - claude-sonnet-4-6  : meilleur rapport qualité/prix (défaut conseillé)
#   - claude-haiku-4-5-20251001 : le moins cher, qualité un peu en dessous
#   - claude-opus-4-8    : qualité maximale, plus cher
MODEL = os.environ.get("POSTS_MODEL", "claude-sonnet-4-6")

# --- Notion (optionnel) ----------------------------------------------------
# Token d'intégration interne : https://www.notion.so/my-integrations
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
# ID de la base « Calendrier éditorial » (32 caractères, dans l'URL de la base)
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "")

# --- Dossier de sortie locale (toujours rempli, même sans Notion) ----------
OUTPUT_DIR = os.environ.get("POSTS_OUTPUT_DIR", "posts/out")

# --- Disclaimer / disclosure conformité (réutilise la voix du bot Telegram) -
# Avertissement de risque (à inclure dès qu'on parle trading/broker, §6.2).
RISK_WARNING = (
    "⚠️ Le trading de CFD/forex comporte un risque de perte en capital. "
    "La majorité des comptes particuliers perdent de l'argent. "
    "Contenu éducatif, pas un conseil en investissement."
)

# Disclosure d'affiliation (à inclure dès qu'on pousse vers FxLift / le
# Telegram dans un but de dépôt, §6.3).
AFFILIATE_DISCLOSURE = "Partenariat rémunéré (FxLift). #ad"

# Piliers de contenu (§3). La clé sert d'identifiant interne, la valeur de
# libellé lisible.
PILIERS = {
    "motivation": "Motivation / mindset",
    "storytelling": "Storytelling",
    "pedagogie": "Pédagogie trading",
    "lifestyle": "Lifestyle / discipline",
}

# Plan hebdomadaire par défaut : ordre des piliers sur la semaine.
# Le storytelling apparaît au moins 1–2 fois (§3.2), la motivation domine (§3.1).
PLAN_HEBDO = [
    "motivation",
    "storytelling",
    "pedagogie",
    "motivation",
    "lifestyle",
    "storytelling",
    "pedagogie",
]
