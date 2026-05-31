"""
Bot Telegram — Le Terminal

Capte l'attribution des nouveaux arrivants pour répartir les commissions
(dont les 20 % des VA). Deux entrées :

  1. Post épinglé DANS le canal (boutons) — voir post_channel.py pour le publier.
     Les clics « Adrien ou Romain / Elisa / Autre » sont enregistrés et confirmés
     par un pop-up privé. Le bouton « Ambassadeur » ouvre une discussion privée.

  2. Discussion PRIVÉE avec le bot (via le bouton Ambassadeur ou un lien en bio).
     Là, le client ÉCRIT lui-même le prénom du VA qui l'a envoyé.

Le bot doit être ADMIN du canal. Lance : python bot.py
"""

import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN, DISCLAIMER, CHANNEL_INVITE_LINK
from db import init_db, upsert_lead
from post_channel import post_question

# Clé dans user_data : le bot attend que la personne tape le prénom du VA
AWAITING_VA = "awaiting_va"


async def ask_va_name(message, context) -> None:
    """Demande à la personne d'écrire elle-même le prénom de l'ambassadeur."""
    context.user_data[AWAITING_VA] = True
    await message.reply_text(
        "Super 🙌 *Écris simplement le prénom de l'ambassadeur* qui t'a parlé "
        "du Terminal :",
        parse_mode="Markdown",
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Discussion privée : via le bouton Ambassadeur (?start=ambassadeur) ou bio."""
    user = update.effective_user
    arg = context.args[0] if context.args else None

    # Venu du bouton « Ambassadeur » -> on lui demande d'écrire le prénom
    if arg == "ambassadeur":
        upsert_lead(user, declared_src="va")
        await ask_va_name(update.message, context)
        return

    # Sinon : sondage classique (visiteur arrivé via un lien en bio)
    keyboard = [
        [InlineKeyboardButton("Adrien ou Romain", callback_data="src:founders")],
        [InlineKeyboardButton("Elisa",            callback_data="src:elisa")],
        [InlineKeyboardButton("Ambassadeur",      callback_data="src:va")],
        [InlineKeyboardButton("Autre",            callback_data="src:autre")],
    ]
    await update.message.reply_text(
        f"Salut {user.first_name} 👋\n\nBienvenue au *Terminal*. "
        "*D'où nous connais-tu ?*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = query.from_user
    data = query.data
    in_channel = bool(query.message) and query.message.chat.type == "channel"

    # En privé, « Ambassadeur » -> on demande d'écrire le prénom du VA
    if data == "src:va" and not in_channel:
        upsert_lead(user, declared_src="va")
        await query.answer()
        await query.edit_message_text(
            "Super 🙌 Écris simplement le *prénom de l'ambassadeur* qui t'a "
            "parlé du Terminal juste en dessous 👇",
            parse_mode="Markdown",
        )
        context.user_data[AWAITING_VA] = True
        return

    # Founders / Elisa / Autre
    mapping = {
        "src:founders": ("founders", "Adrien & Romain"),
        "src:elisa":    ("elisa",    "Elisa"),
        "src:autre":    ("autre",    "une autre source"),
    }
    declared, label = mapping[data]
    upsert_lead(user, declared_src=declared)

    if in_channel:
        # Post public partagé : on ne le modifie PAS, on confirme en privé
        await query.answer(f"Merci ! C'est noté : {label} ✅", show_alert=True)
    else:
        await query.answer()
        await query.edit_message_text(
            f"Merci ! On note que tu viens de *{label}* 🙌\n\n"
            f"➡️ Le canal gratuit : {CHANNEL_INVITE_LINK}{DISCLAIMER}",
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Récupère le prénom du VA tapé par la personne."""
    if not context.user_data.get(AWAITING_VA):
        return  # message hors contexte : on ignore

    va_name = update.message.text.strip()[:50]
    upsert_lead(update.effective_user, declared_src="va", va_name=va_name)
    context.user_data[AWAITING_VA] = False

    await update.message.reply_text(
        f"Parfait, on note que tu viens de *{va_name}* 🙌\n\n"
        f"➡️ Le canal gratuit : {CHANNEL_INVITE_LINK}{DISCLAIMER}",
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


async def _post_init(app: Application) -> None:
    """Publie le post du canal au démarrage si POST_ON_START=1 (déploiement 1 clic)."""
    if os.environ.get("POST_ON_START") == "1":
        await post_question(app.bot)


def main() -> None:
    init_db()
    app = Application.builder().token(BOT_TOKEN).post_init(_post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    print("Bot démarré. Ctrl+C pour arrêter.")
    app.run_polling()


if __name__ == "__main__":
    main()
