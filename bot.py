"""
Bot Telegram — Le Terminal

Capte l'attribution des nouveaux arrivants pour répartir les commissions
(dont les 20 % des VA). Deux entrées :

  1. Post épinglé DANS le canal (boutons) — voir post_channel.py pour le publier.
     Les clics « Adrien ou Romain / Elisa / Autre » sont enregistrés et confirmés
     par un pop-up privé. Le bouton « Un ambassadeur » ouvre une discussion privée.

  2. Discussion PRIVÉE avec le bot (via le bouton ambassadeur ou un lien en bio).
     Là, on peut afficher discrètement la liste des VA sans l'exposer publiquement.

Le bot doit être ADMIN du canal. Lance : python bot.py
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from config import BOT_TOKEN, VA, DISCLAIMER, CHANNEL_INVITE_LINK
from db import init_db, upsert_lead


def va_keyboard() -> InlineKeyboardMarkup:
    """Sous-menu privé listant les VA (jamais affiché dans le canal)."""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(name, callback_data=f"va:{key}")]
         for key, name in VA.items()]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Discussion privée : via le bouton ambassadeur (?start=ambassadeur) ou bio."""
    user = update.effective_user
    arg = context.args[0] if context.args else None

    # Venu du bouton « Un ambassadeur » -> on demande discrètement lequel
    if arg == "ambassadeur":
        upsert_lead(user, declared_src="va")
        await update.message.reply_text(
            "Merci d'être passé par un de nos ambassadeurs 🙌\n\n"
            "Lequel t'a parlé du Terminal ?",
            reply_markup=va_keyboard(),
        )
        return

    # Sinon : sondage classique (visiteur arrivé via un lien en bio)
    keyboard = [
        [InlineKeyboardButton("Adrien ou Romain", callback_data="src:founders")],
        [InlineKeyboardButton("Elisa",            callback_data="src:elisa")],
        [InlineKeyboardButton("Un ambassadeur",   callback_data="src:va")],
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

    # Choix d'un VA précis (toujours en privé)
    if data.startswith("va:"):
        va_name = VA.get(data.split(":", 1)[1], "Inconnu")
        upsert_lead(user, declared_src="va", va_name=va_name)
        await query.answer("C'est noté ✅")
        await query.edit_message_text(
            f"Parfait, on note que tu viens de *{va_name}* 🙌{DISCLAIMER}",
            parse_mode="Markdown",
        )
        return

    # En privé, « Un ambassadeur » ouvre le sous-menu des VA
    if data == "src:va" and not in_channel:
        upsert_lead(user, declared_src="va")
        await query.answer()
        await query.edit_message_text(
            "Super ! Quel ambassadeur t'a parlé du Terminal ?",
            reply_markup=va_keyboard(),
        )
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


def main() -> None:
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_button))
    print("Bot démarré. Ctrl+C pour arrêter.")
    app.run_polling()


if __name__ == "__main__":
    main()
