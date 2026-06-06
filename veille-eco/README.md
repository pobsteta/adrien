# Le Terminal Économies

Un **site statique** au look « terminal financier » (fond sombre, accent
émeraude, ticker défilant) qui publie chaque matin une revue de presse
économique. Chaque annonce est une carte cliquable avec un bouton vers la
source. Deux sources de contenu :

- **automatique** : agrégation de flux RSS de médias et institutions ;
- **manuelle** : votre sélection éditoriale du jour, mise en avant en tête de page.

Sortie = des fichiers **HTML/CSS** dans `output/` : gratuit à héberger, rapide,
régénérable d'une commande. Pas de framework web, pas de base de données.

## Stack

- Python 3
- [`feedparser`](https://pypi.org/project/feedparser/) — lecture des flux RSS/Atom
- [`jinja2`](https://pypi.org/project/Jinja2/) — gabarits HTML

```bash
pip install feedparser jinja2
```

## Arborescence

```
veille-eco/
├── sources/feeds.json      # sources RSS éditables (name, url, category, weight)
├── data/manual.json        # votre sélection du jour (title, url, source, summary, date)
├── data/aggregated.json    # produit par aggregate.py (ne pas éditer à la main)
├── scripts/aggregate.py    # récupère, normalise, déduplique, filtre, trie les flux
├── scripts/build.py        # assemble auto + manuel et génère le site
├── templates/              # gabarits Jinja2 + style.css
├── output/                 # site généré (à héberger)
├── publish.sh              # enchaîne aggregate.py puis build.py
└── README.md
```

Le site comporte trois types de pages : l'**édition du jour** (`index.html`,
avec un bandeau de présentation et un lien « En savoir plus »), les **archives**
(`archives/`), et une page **« À propos »** (`a-propos.html`) qui détaille la
mission, le fonctionnement et une FAQ. Toutes partagent la barre latérale
(partiel `templates/_sidebar.html`).

## Utilisation

```bash
# Tout régénérer (flux + site) :
./publish.sh

# Forcer une date d'édition (utile pour rejouer une archive) :
./publish.sh 2026-06-06

# Ou étape par étape :
python3 scripts/aggregate.py          # -> data/aggregated.json
python3 scripts/build.py              # -> output/
```

Ouvrez ensuite `output/index.html` dans un navigateur. Pour héberger, déposez
le contenu de `output/` sur n'importe quel hébergement statique (GitHub Pages,
Netlify, un simple serveur de fichiers…).

## Configurer les sources

Éditez `sources/feeds.json`. Chaque entrée :

```json
{ "name": "Le Monde – Économie", "url": "https://…/rss.xml", "category": "France", "weight": 4 }
```

La navigation se fait via une **barre latérale gauche rétractable** (façon
YouTube) : l'icône ☰ en haut à gauche la replie/déplie, et l'état est mémorisé
d'une page à l'autre (`templates/app.js`, copié dans `output/app.js`). Sur
mobile, elle s'ouvre en surimpression. Le menu liste *Édition du jour*,
*Archives*, le groupe *L'édition* (À la une, Flash, La sélection) et le groupe
*Zones* (chaque rubrique avec son nombre d'annonces).

- `category` regroupe les articles en **rubriques géographiques** affichées
  dans cet ordre : *Europe*, *Amériques*, *France*, *Institutions*, *Asie*,
  *International* (ordre réglable via `CATEGORY_ORDER` dans `build.py` ;
  toute autre valeur apparaît ensuite). Il suffit de changer le `category`
  d'une source pour la déplacer de rubrique.
- `weight` (1–5) influence le tri : un poids fort remonte la source, et le
  mieux classé devient l'article **à la une**.

En plus des rubriques, une section **⚡ Flash** affiche automatiquement les
annonces les plus récentes (tous flux confondus), réglable en haut de
`build.py` : `FLASH_COUNT` (nombre) et `FLASH_MAX_AGE_HOURS` (fraîcheur max).

> ⚠️ **Vérifiez les URLs des flux** livrées par défaut : elles changent souvent
> selon les éditeurs. Remplacez-les par les flux RSS officiels à jour.

## Ajouter votre sélection du jour

Éditez `data/manual.json`. Ces items s'affichent **en premier**, dans
l'encadré sombre « La sélection ». Le champ `date` (AAAA-MM-JJ) filtre
l'affichage : seuls les items à la date de l'édition apparaissent.

```json
{
  "title": "Pourquoi la désinflation française résiste mieux que prévu",
  "url": "https://…",
  "source": "Analyse maison",
  "summary": "Décryptage en une à deux phrases…",
  "date": "2026-06-06"
}
```

## Réglages de l'agrégation

En haut de `scripts/aggregate.py` (constantes) :

| Constante          | Rôle                                          | Défaut |
|--------------------|-----------------------------------------------|--------|
| `LOOKBACK_HOURS`   | fenêtre de fraîcheur                           | 36 h   |
| `MAX_PER_SOURCE`   | plafond d'articles par source                  | 8      |
| `MAX_TOTAL`        | plafond global d'articles                      | 60     |
| `EXCERPT_MAX_CHARS`| longueur max de l'extrait                       | 280    |
| `REQUEST_TIMEOUT`  | délai avant d'abandonner un flux injoignable    | 15 s   |

## Droit d'auteur

Le site **n'agrège que des flux RSS** et n'en republie que le **titre + un
court extrait + un lien retour** vers la source, toujours créditée. L'article
complet n'est jamais reproduit.

## Et l'IA ?

Volontairement **pas encore** d'appel à une API ni de résumé automatique.
Le code est toutefois prêt à l'accueillir :

- chaque article porte un champ **`summary` distinct de `excerpt`**. Tant que
  `summary` est vide, l'affichage retombe sur l'extrait du flux
  (`resolve_summary` dans `build.py`).
- l'étape de résumé sera un **module isolé et optionnel** intercalé entre
  `aggregate.py` et `build.py` : il lira `data/aggregated.json`, remplira le
  champ `summary`, et réécrira le fichier. Aucun autre code à changer.
