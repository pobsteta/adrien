# Déploiement sur Koyeb 🇫🇷 (gratuit)

Koyeb est un hébergeur français avec un palier **gratuit**. Le bot tourne en
continu (mode *polling*) → on le déploie comme un service **Worker** (pas de
port web). Données hébergeables en **UE (Francfort)**.

---

## Étape 1 — Côté Telegram (à faire avant)

1. Crée le bot via **@BotFather** → récupère le **token** + le **@username**.
2. Ajoute le bot comme **administrateur de `@LeTerminalFx`**, avec le droit
   **« Épingler les messages »**.

---

## Étape 2 — Déployer sur Koyeb

1. Va sur **[koyeb.com](https://www.koyeb.com)** → crée un compte (connexion GitHub).
2. **Create Service** → **GitHub** → autorise l'accès → choisis le dépôt
   **`pobsteta/adrien`** et la branche **`claude/exciting-darwin-3UzlB`**.
3. **Builder** : Koyeb détecte le `Dockerfile` automatiquement → laisse tel quel.
4. **Service type** : choisis **Worker** ⚠️ (important : pas de « Web », car le
   bot n'expose aucun port HTTP).
5. **Region** : **Frankfurt** (UE).
6. **Instance** : **Free** (Nano).
7. **Environment variables** — ajoute :

   | Variable | Valeur |
   |---|---|
   | `BOT_TOKEN` | ton token BotFather |
   | `BOT_USERNAME` | le @username du bot, **sans @** |
   | `CHANNEL_ID` | `@LeTerminalFx` |
   | `POST_ON_START` | `1` *(uniquement pour le 1er lancement)* |

8. **Deploy**.

---

## Étape 3 — Publier la question (une seule fois)

- Avec `POST_ON_START=1`, au démarrage le bot poste + épingle la question dans
  le canal.
- Ensuite, **repasse `POST_ON_START` à `0`** et redéploie (sinon il reposte le
  message à chaque redémarrage).

---

## Étape 4 — Vérifier

- Le post à 4 boutons est épinglé dans `@LeTerminalFx`.
- « Adrien ou Romain » → pop-up « C'est noté ✅ ».
- « Ambassadeur » → ouvre le bot en privé et demande d'écrire le prénom du VA.

---

## ⚠️ Important : persistance des données

Le tier gratuit de Koyeb **n'a pas de disque persistant** : le fichier
`attribution.db` est **effacé à chaque redéploiement**.

Pour ne pas perdre tes leads (et donc le calcul des 20 %), recommandé :
**logguer chaque lead dans un canal Telegram privé** (gratuit et permanent).
Demande-moi de l'ajouter — c'est rapide et ça sécurise tout.
