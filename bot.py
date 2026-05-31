"""
Bot Telegram — Le Terminal
Capte l'attribution des nouveaux arrivants (founders / Elisa / VA / autre)
pour répartir correctement les commissions (dont les 20 % des VA).

Lib : python-telegram-bot >= 21
Lance : python bot.py
"""

import os
import sqlite3
from datetime import datetime, timezone

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# --------------------------------------------------------------------------
# CONFIG  (à adapter)
# --------------------------------------------------------------------------
BOT_TOKEN = os.environ["BOT_TOKEN"]            # donné par @BotFather
CHANNEL_INVITE_LINK = "https://t.me/+xxxxxxxx"  # lien d'invitation du canal gratuit

# Tes VA actuels. La clé sert dans les liens de parrainage (t.me/Bot?start=va_marie)
VA = {
    "va_marie": "Marie",
    "va_karim": "Karim",
    "va_sofia": "Sofia",
    "va_lucas": "Lucas",
    "va_ines": "Inès",
}

DB_PATH = "attribution.db"

DISCLAIMER = (
    "\n\n⚠️ _Le trading de CFD/forex comporte un risque de perte en capital. "
    "La majorité des comptes particuliers perdent de l'argent. "
    "Contenu éducatif — pas un conseil en investissement. Partenariat rémunéré (FxLift)._"
)


# --------------------------------------------------------------------------
# BASE DE DONNÉES
# --------------------------------------------------------------------------
def init_db() -> None:
    con = sqlite3.connect(DB_PATH)
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            user_id        INTEGER PRIMARY KEY,
            username       TEXT,
            first_name     TEXT,
            deeplink_src   TEXT,   -- source captée automatiquement via le lien
            declared_src   TEXT,   -- source déclarée via le sondage
            va_name        TEXT,   -- nom du VA si applicable
            created_at     TEXT
        )
        """
    )
    con.commit()
    con.close()


def upsert_lead(user, deeplink_src=None, declared_src=None, va_name=None):
    con = sqlite3.connect(DB_PATH)
    now = datetime.now(timezone.utc).isoformat()
    con.execute(
        """
        INSERT INTO leads (user_id, username, first_name, deeplink_src,
                           declared_src, va_name, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username     = excluded.username,
            first_name   = excluded.first_name,
            deeplink_src = COALESCE(excluded.deeplink_src, leads.deeplink_src),
            declared_src = COALESCE(excluded.declared_src, leads.declared_src),
            va_name      = COALESCE(excluded.va_name,      leads.va_name)
        """,
        (user.id, user.username, user.first_name,
         deeplink_src, declared_src, va_name, now),
    )
    con.commit()
    con.close()


# --------------------------------------------------------------------------
# HANDLERS
# --------------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user

    # 1) Attribution AUTOMATIQUE via le lien de parrainage (t.me/Bot?start=va_marie)
    deeplink_src = context.args[0] if context.args else None
    va_name = VA.get(deeplink_src) if deeplink_src else None
    upsert_lead(user, deeplink_src=deeplink_src, va_name=va_name)

    # 2) Sondage (filet de sécurité / confirmation)
    keyboard = [
        [InlineKeyboardButton("Adrien ou Romain", callback_data="src:founders")],
        [InlineKeyboardButton("Elisa",            callback_data="src:elisa")],
        [InlineKeyboardButton("Un ambassadeur / partenaire", callback_data="src:va")],
        [InlineKeyboardButton("Autre",            callback_data="src:autre")],
    ]
    await update.message.reply_text(
        f"Salut {user.first_name} 👋\n\n"
        "Bienvenue au *Terminal*. Pour mieux te connaître : "
        "*d'où nous connais-tu ?*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = query.data

    # L'utilisateur a choisi « Un ambassadeur » -> on affiche la liste des VA
    if data == "src:va":
        keyboard = [
            [InlineKeyboardButton(name, callback_data=f"va:{key}")]
            for key, name in VA.items()
        ]
        await query.edit_message_text(
            "Super ! Quel ambassadeur t'a parlé du Terminal ?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    # Choix d'un VA précis
    if data.startswith("va:"):
        key = data.split(":", 1)[1]
        va_name = VA.get(key, "Inconnu")
        upsert_lead(user, declared_src="va", va_name=va_name)
        await finish(query, f"Merci ! On note que tu viens de *{va_name}* 🙌")
        return

    # Founders / Elisa / Autre
    mapping = {
        "src:founders": ("founders", "Adrien & Romain"),
        "src:elisa":    ("elisa",    "Elisa"),
        "src:autre":    ("autre",    "autre source"),
    }
    declared, label = mapping[data]
    upsert_lead(user, declared_src=declared)
    await finish(query, f"Merci ! On note que tu viens de *{label}* 🙌")


async def finish(query, line: str) -> None:
    """Message final commun : remercie + donne le canal + disclaimer."""
    await query.edit_message_text(
        f"{line}\n\n"
        f"➡️ Rejoins le canal gratuit ici : {CHANNEL_INVITE_LINK}"
        f"{DISCLAIMER}",
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


# --------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------
def main() -> None:
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_button))
    print("Bot démarré. Ctrl+C pour arrêter.")
    app.run_polling()


if __name__ == "__main__":
    main()
