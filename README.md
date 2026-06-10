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
   - *Ambassadeur* → ouvre une **discussion privée** avec le bot, qui demande à
     la personne d'**écrire elle-même le prénom du VA** qui l'a envoyée.

> Aucune liste de VA à maintenir : le client tape le prénom. Les VA envoient
> leur audience vers le canal, et la personne indique de qui elle vient via le
> bouton « Ambassadeur ».

## Rapport de commissions

```bash
python commissions.py
```

Affiche les leads par source et par VA — base de calcul des 20 %.

## Conformité

Le post et les messages incluent le disclaimer risque + disclosure d'affiliation
(FxLift). À ne pas retirer.

## Questionnaire « Étude utilisateurs » (`docs/index.html`)

Page web autonome (un seul fichier, zéro dépendance) qui reprend la DA du
Terminal : fond `#05080C`, accent bleu glacier `#9DC8F6`, Space Grotesk.
Les 19 questions de l'étude, toutes facultatives, bloc bêta + e-mail en premier,
brouillon sauvegardé en local, barre de progression, responsive mobile.

**Publier (GitHub Pages)** : *Settings → Pages → Deploy from a branch* →
branche `main`, dossier `/docs`. Le formulaire est alors en ligne sur
`https://pobsteta.github.io/adrien/`.

**Réponses** : envoyées par e-mail (mise en forme tableau) via FormSubmit à
`pascal.obstetar@gmail.com`. ⚠️ À la **première** soumission, FormSubmit envoie
un e-mail d'activation à cette adresse — cliquer le lien une fois, puis tout
arrive automatiquement. Pour changer de destinataire : modifier `ENDPOINT` et
`FALLBACK_EMAIL` dans le script en bas de `docs/index.html`.

Si tu préfères un export CSV/Sheets natif, le guide Tally/Google Forms reste
valable — cette page peut servir de version « look premium » en parallèle.
