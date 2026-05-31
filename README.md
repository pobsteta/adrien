# Bot Telegram — Le Terminal

Bot d'**attribution** des nouveaux arrivants : il demande à chaque personne d'où
elle vient (Adrien/Romain, Elisa, un VA/ambassadeur, ou autre) et enregistre la
réponse pour répartir les commissions — notamment les **20 % des VA**.

## Installation

```bash
pip install -r requirements.txt
export BOT_TOKEN="le_token_donné_par_BotFather"
python bot.py
```

## Configuration

Dans `bot.py` :
- `CHANNEL_INVITE_LINK` : le lien d'invitation de ton canal gratuit.
- `VA` : la liste de tes ambassadeurs (clé technique → nom affiché).

## Les liens de parrainage (attribution automatique)

Chaque VA partage son **propre lien** au lieu du lien brut du canal :

```
https://t.me/LeTerminalBot?start=va_marie
https://t.me/LeTerminalBot?start=va_karim
...
```

Quand quelqu'un clique et lance le bot, la source est captée **automatiquement**
(même s'il ne répond pas au sondage). Tu mets ces liens dans les bios TikTok/Insta
de chaque VA, et dans celles d'Adrien/Romain/Elisa (`?start=founders`, `?start=elisa`).

## Funnel

```
TikTok / Insta  →  t.me/LeTerminalBot?start=<source>  →  sondage  →  lien du canal + FxLift
```

## Rapport de commissions

```bash
python commissions.py
```

Affiche le nombre de leads par source et par VA — base de calcul des 20 %.

## Conformité

Le message final inclut le disclaimer risque + disclosure d'affiliation (FxLift),
conformément aux règles du projet. À ne pas retirer.
