# Le Terminal — Générateur de posts LinkedIn & X (Adrien)

Système qui **génère**, **vérifie (conformité)** et **range pour validation** des
posts LinkedIn et X pour Adrien — calibrés réseau par réseau, dans la voix
d'Adrien, avec garde-fous réglementaires codés en dur.

> ⚠️ **Rien n'est publié automatiquement.** Le système s'arrête à la revue
> humaine : tu valides dans Notion, puis tu programmes dans Publer. C'est voulu
> (promotion financière réglementée, public débutant).

---

## 1. Le pipeline en 4 étapes

```
1. GÉNÉRATION        Python + API Claude → 1 idée = 1 version LinkedIn + 1 thread X
        ↓
2. CONFORMITÉ        filtre codé en dur (mots interdits + avertissement risque + #ad)
        ↓
3. REVUE HUMAINE     base Notion « Calendrier éditorial » (statut Brouillon → Validé)
        ↓
4. PUBLICATION       toi → copier-coller dans Publer (gratuit) → programmation
```

| Fichier | Rôle |
|---|---|
| `config.py` | Réglages : clé API, modèle, IDs Notion, disclaimers, piliers, plan hebdo |
| `prompts.py` | **Prompt système** : voix d'Adrien + piliers + codes réseaux + conformité |
| `hooks.py` | Banque de **hooks** LinkedIn/X + **angles de storytelling** |
| `compliance.py` | **Filtre de conformité** (mots interdits, checklist risque/disclosure) |
| `generate.py` | **Moteur** : génère la batch, vérifie, sauve en local, pousse vers Notion |
| `notion_sync.py` | Envoi des posts dans la base Notion (1 page par plateforme) |

---

## 2. Installation (commande par commande)

> Pré-requis : Python 3.10+. Vérifie avec `python --version`.

```bash
# 1. Installer les dépendances
pip install -r posts/requirements.txt

# 2. Créer ton fichier de secrets à partir du modèle
cp posts/.env.example posts/.env
```

Ouvre `posts/.env` et remplis les valeurs (voir §3 et §4 ci-dessous), puis
charge-le dans ton terminal **à chaque session** :

```bash
set -a; source posts/.env; set +a
```

---

## 3. Créer ta clé API Anthropic (obligatoire)

1. Va sur **https://console.anthropic.com** et crée un compte.
2. Ajoute un moyen de paiement (facturation à l'usage, pas d'abonnement).
   → Génère ~10 posts/semaine ≈ **quelques centimes à 0,50 $/semaine** en Sonnet.
3. Menu **Settings → API Keys → Create Key**. Copie la clé (commence par `sk-ant-`).
4. Colle-la dans `posts/.env` :
   ```
   ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
   ```

> Pour réduire encore le coût : mets `POSTS_MODEL=claude-haiku-4-5-20251001`
> dans `.env` (moins cher, qualité un peu en dessous).

---

## 4. Connecter Notion (déjà préparé)

La base **« 📅 Calendrier éditorial — LinkedIn & X (Adrien) »** a déjà été créée
dans ton espace, sous la page **📈 LE TERMINAL**.

- **Database ID** : `2092fe930d9d41cab659d692eff42866`

Pour que le script puisse y écrire, il faut une clé d'intégration Notion :

1. Va sur **https://www.notion.so/my-integrations → New integration**.
   Nomme-la « Le Terminal Posts », type *Internal*. Copie le **Internal
   Integration Secret** (commence par `secret_` ou `ntn_`).
2. Ouvre la base dans Notion → menu **⋯ (en haut à droite) → Connections →
   Add connections →** choisis ton intégration. (Sans cette étape, l'API n'a
   pas le droit d'écrire dans la base.)
3. Remplis `posts/.env` :
   ```
   NOTION_TOKEN=secret_xxxxxxxx
   NOTION_DATABASE_ID=2092fe930d9d41cab659d692eff42866
   ```

> Notion est **optionnel**. Sans ces variables, les posts sont quand même
> écrits en local dans `posts/out/` (Markdown + JSON), prêts à relire.

---

## 5. Utilisation

```bash
# Tester le pipeline SANS appeler l'API (ni coût) :
python posts/generate.py --dry-run --no-notion

# Vérifier que le filtre de conformité fonctionne :
python posts/compliance.py

# Générer la vraie batch de la semaine (plan hebdo = 7 posts variés) :
python posts/generate.py

# Variantes :
python posts/generate.py --count 5        # 5 posts
python posts/generate.py --no-notion      # local seulement, sans Notion
```

Sortie :
- `posts/out/batch_AAAA-WSS.md` → version lisible (à relire en premier).
- `posts/out/batch_AAAA-WSS.json` → données brutes.
- Dans Notion : 2 pages par post (LinkedIn + X), statut **Brouillon**.

---

## 6. Ton workflow hebdomadaire (≈ 15 min)

1. `python posts/generate.py` (le lundi par exemple).
2. Ouvre le `.md` ou la base Notion. **Lis chaque post.**
3. Regarde la colonne **Conformité** :
   - ✅ **OK** : relis quand même le ton, puis passe le **Statut** à *Validé*.
   - ⚠️ **À revoir** : une tournure peut ressembler à un conseil perso → corrige.
   - ⛔ **Bloqué** : non conforme (promesse de gain, ou avertissement de risque
     manquant). **Ne publie pas** : corrige le texte ou régénère.
4. Pour chaque post *Validé* : copie le texte → colle dans **Publer** → programme
   à la **Date prévue**. Passe le Statut à *Publié*.

> Rappel Publer/X : le **lien** (Telegram/FxLift) va dans le **dernier tweet** du
> thread, jamais le premier. Sur LinkedIn, lien en **commentaire**.

---

## 7. Conformité — ce qui est codé en dur (§6 du brief)

Le filtre (`compliance.py`) **bloque** automatiquement avant la revue :

- ❌ promesses de gain / « sans risque » / « devenir riche » / rendements
  garantis / chiffres de profit (« +50% par mois »…) ;
- ❌ un post qui parle de trading **sans** l'avertissement de risque ;
- ❌ un post qui pousse vers FxLift/Telegram **sans** la disclosure `#ad` /
  partenariat ;
- ⚠️ signale (sans bloquer) les tournures de conseil personnalisé.

Les textes exacts d'avertissement et de disclosure sont dans `config.py`
(`RISK_WARNING`, `AFFILIATE_DISCLOSURE`) — modifiables en un seul endroit.

> Le filtre est un **garde-fou**, pas un avocat. La validation humaine reste
> obligatoire. Adrien réside à Malte sans structure légale en place : la
> prudence éditoriale doit être maximale.

---

## 8. Personnaliser

- **Voix / règles** : édite le `SYSTEM_PROMPT` dans `prompts.py`.
- **Accroches** : ajoute des lignes dans `hooks.py` (listes `HOOKS_LINKEDIN`,
  `HOOKS_X`, `ANGLES_STORYTELLING`).
- **Rythme / piliers de la semaine** : modifie `PLAN_HEBDO` dans `config.py`.
- **Mots interdits** : complète les listes de `compliance.py`.

---

## 9. Coûts (tout signalé)

| Poste | Coût |
|---|---|
| API Claude (~10 posts/sem., Sonnet) | ~0,10–0,50 $/sem. |
| Notion | Gratuit |
| Publer (free tier) | 0 $ pour démarrer (~12 $/mois si tu passes à l'auto) |
| API X / LinkedIn directe | **non utilisée** (aurait coûté ~200 $/mois + validation) |
