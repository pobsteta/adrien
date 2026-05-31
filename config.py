"""Configuration partagée du bot Le Terminal."""

import os

BOT_TOKEN = os.environ["BOT_TOKEN"]                       # donné par @BotFather
BOT_USERNAME = os.environ.get("BOT_USERNAME", "LeTerminalBot")  # sans le @
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@LeTerminal")  # @public ou -100xxxx si privé

CHANNEL_INVITE_LINK = "https://t.me/+xxxxxxxx"  # lien du canal (pour les visiteurs via bio)

# Tes ambassadeurs (VA). Les noms restent PRIVÉS : ils n'apparaissent qu'en
# discussion privée, jamais dans le post public du canal.
VA = {
    "va_marie": "Marie",
    "va_karim": "Karim",
    "va_sofia": "Sofia",
    "va_lucas": "Lucas",
    "va_ines": "Inès",
}

DB_PATH = os.environ.get("DB_PATH", "attribution.db")  # pointe vers un volume persistant en prod

DISCLAIMER = (
    "\n\n⚠️ _Trading de CFD/forex = risque de perte en capital. La majorité des "
    "comptes particuliers perdent de l'argent. Contenu éducatif, pas un conseil "
    "en investissement. Partenariat rémunéré (FxLift)._"
)
