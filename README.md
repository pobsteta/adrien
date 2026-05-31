# Bot Telegram — Le Terminal

Bot d'**attribution** des nouveaux arrivants : il demande d'où vient chaque
personne (Adrien/Romain, Elisa, un ambassadeur/VA, ou autre) et enregistre la
réponse pour répartir les commissions — notamment les **20 % des VA**.

## Fichiers

| Fichier | Rôle |
|---|---|
| `config.py` | Token, username du bot, canal, liste des VA, disclaimer |
| `db.py` | Stockage SQLite des leads |
| `bot.py` | Bot principal (à laisser tourner) — capte les clics |
| `post_channel.py` | Publie + épingle la question dans le canal (une fois) |
| `commissions.py` | Rapport leads par source / par VA |

## Installation

```bash
pip install -r requirements.txt
export BOT_TOKEN="le_token_de_BotFather"
export BOT_USERNAME="LeTerminalBot"   # sans @
export CHANNEL_ID="@LeTerminal"       # ou -100xxxx si canal privé
```

Puis renseigne `CHANNEL_INVITE_LINK` et la liste `VA` dans `config.py`.

## Comment ça marche dans le canal (Option B)

1. Le bot doit être **administrateur** du canal (avec droit d'épingler).
2. `python post_channel.py` publie un message épinglé avec 4 boutons :
   **Adrien ou Romain · Elisa · Un ambassadeur · Autre**.
3. `python bot.py` tourne en continu et capte les clics :
   - *Adrien/Romain*, *Elisa*, *Autre* → enregistré + confirmation en pop-up
     privé (le post public n'est pas modifié).
   - *Un ambassadeur* → ouvre une **discussion privée** avec le bot, qui demande
     discrètement **quel VA** (les noms des VA ne sont jamais affichés
     publiquement dans le canal).

> Les VA n'ont pas de lien dédié : ils envoient leur audience vers le canal
> d'Adrien/Romain, et la personne indique elle-même de quel VA elle vient via
> le bouton « Un ambassadeur ».

## Rapport de commissions

```bash
python commissions.py
```

Affiche les leads par source et par VA — base de calcul des 20 %.

## Conformité

Le post et les messages incluent le disclaimer risque + disclosure d'affiliation
(FxLift). À ne pas retirer.
