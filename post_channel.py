"""
Publie (et épingle) la question d'attribution DANS le canal.

Le bot doit être ADMIN du canal avec le droit d'épingler.
Utilisable de deux façons :
  - en ligne de commande, une fois :         python post_channel.py
  - automatiquement au démarrage du bot :     POST_ON_START=1 (voir bot.py)
"""

import asyncio

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from config import BOT_TOKEN, BOT_USERNAME, CHANNEL_ID, DISCLAIMER


async def post_question(bot: Bot) -> None:
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Adrien ou Romain", callback_data="src:founders")],
        [InlineKeyboardButton("Elisa",            callback_data="src:elisa")],
        # Ouvre une discussion PRIVÉE où la personne écrit le prénom du VA
        [InlineKeyboardButton("Ambassadeur",
                              url=f"https://t.me/{BOT_USERNAME}?start=ambassadeur")],
        [InlineKeyboardButton("Autre",            callback_data="src:autre")],
    ])

    msg = await bot.send_message(
        chat_id=CHANNEL_ID,
        text=("👋 *Bienvenue au Terminal !*\n\n"
              "Pour mieux te connaître, dis-nous *d'où tu nous connais* 👇"
              f"{DISCLAIMER}"),
        reply_markup=keyboard,
        parse_mode="Markdown",
    )
    await bot.pin_chat_message(CHANNEL_ID, msg.message_id, disable_notification=True)
    print(f"Message {msg.message_id} posté et épinglé dans {CHANNEL_ID}.")


async def _main() -> None:
    await post_question(Bot(BOT_TOKEN))


if __name__ == "__main__":
    asyncio.run(_main())
