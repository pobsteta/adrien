"""Configuration partagée du bot Le Terminal."""

import os

BOT_TOKEN = os.environ["BOT_TOKEN"]                       # donné par @BotFather
BOT_USERNAME = os.environ.get("BOT_USERNAME", "LeTerminalBot")  # sans le @
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@LeTerminalFx")  # @public ou -100xxxx si privé

CHANNEL_INVITE_LINK = "https://t.me/LeTerminalFx"  # lien du canal (pour les visiteurs via bio)

# Pas de liste figée de VA : quand un client choisit « Ambassadeur », il écrit
# lui-même le prénom du VA. Plus souple (aucune modif quand un VA arrive/part).

DB_PATH = os.environ.get("DB_PATH", "attribution.db")  # pointe vers un volume persistant en prod

DISCLAIMER = (
    "\n\n⚠️ _Trading de CFD/forex = risque de perte en capital. La majorité des "
    "comptes particuliers perdent de l'argent. Contenu éducatif, pas un conseil "
    "en investissement. Partenariat rémunéré (FxLift)._"
)
