# Déploiement 1 clic — Bot Le Terminal

Objectif : mettre le bot en ligne 24/7 avec un minimum de manipulations.
Tu ne touches jamais à du code : tu crées le bot, tu colles 3 valeurs, c'est tout.

---

## Étape 1 — Créer le bot (côté Telegram, ~2 min)

1. Dans Telegram, ouvre **@BotFather** → `/newbot`.
2. Donne un nom et un **@username** (ex. `LeTerminalBot`).
3. BotFather te donne un **token** secret (ex. `123456:ABC-...`). Garde-le.
4. Ajoute le bot comme **administrateur de ton canal**, avec le droit
   **« Épingler les messages »** (Paramètres du canal → Administrateurs → Ajouter).

> ⚠️ Ne partage ton token avec personne et ne le mets jamais dans le code.

---

## Étape 2 — Déployer (au choix : Railway ou Render)

### Option Railway (le plus simple)

1. Va sur [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
   → choisis ce dépôt. Railway détecte le `Dockerfile` automatiquement.
2. Onglet **Variables**, ajoute :
   | Variable | Valeur |
   |---|---|
   | `BOT_TOKEN` | le token de BotFather |
   | `BOT_USERNAME` | `LeTerminalBot` (sans @) |
   | `CHANNEL_ID` | `@LeTerminal` (ou `-100xxxx` si canal privé) |
   | `POST_ON_START` | `1` *(uniquement pour le 1er lancement, voir étape 3)* |
3. (Recommandé) Ajoute un **Volume** monté sur `/data` et la variable
   `DB_PATH=/data/attribution.db` pour ne pas perdre les leads à chaque redéploiement.
4. **Deploy**. Le bot démarre.

### Option Render

1. Va sur [render.com](https://render.com) → **New** → **Blueprint** → choisis ce dépôt.
   Render lit `render.yaml` (worker + disque persistant déjà configurés).
2. Renseigne `BOT_TOKEN`, `BOT_USERNAME`, `CHANNEL_ID` quand il les demande.
3. **Apply**.

---

## Étape 3 — Publier la question dans le canal (une seule fois)

Le message épinglé avec les boutons doit être posté **une seule fois**.

- Mets `POST_ON_START=1`, lance/redéploie → le bot poste + épingle le message.
- **Repasse ensuite `POST_ON_START` à `0`** et redéploie, sinon il reposterait
  le message à chaque redémarrage.

---

## Étape 4 — Vérifier

- Le post à 4 boutons est épinglé en haut du canal.
- Clique « Adrien ou Romain » → un petit pop-up « C'est noté ✅ » apparaît.
- Clique « Un ambassadeur » → ça ouvre le bot en privé et demande quel VA.

---

## Voir les leads / commissions

Les réponses sont stockées dans `attribution.db`. Pour le rapport :

```bash
python commissions.py
```

> Sur Railway/Render, lance-le depuis le **shell** du service, ou récupère le
> fichier `attribution.db` depuis le volume. (Pour un suivi plus pratique, on
> pourra brancher un export Google Sheets — dis-le moi.)
