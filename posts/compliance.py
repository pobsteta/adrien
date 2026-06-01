"""Filtre de conformité — règles NON négociables (§6).

Codé en dur. Rien ne doit arriver en couche de revue humaine sans être passé
par ici. Le filtre rend un verdict par post :

    - OK     : aucun problème détecté.
    - WARN   : à vérifier par un humain (ex. ton ambigu), mais pas bloquant.
    - BLOCK  : non conforme, ne PAS publier en l'état.

Principe : on préfère un faux positif (bloquer à tort) à un faux négatif
(laisser passer une promesse de gain illégale). Le public est composé de
débutants et il s'agit d'une promotion financière réglementée.
"""

import re
from dataclasses import dataclass, field

# --- 1. Expressions interdites → BLOCK (§6.1) ------------------------------
# Promesses de gain, absence de risque, enrichissement, garanties.
INTERDITS = [
    r"gains?\s+faciles?",
    r"argent\s+facile",
    r"sans\s+(aucun\s+)?risque",
    r"aucun\s+risque",
    r"z[ée]ro\s+risque",
    r"risque\s+z[ée]ro",
    r"devenir\s+riche",
    r"devenez\s+riche",
    r"riche\s+(rapidement|facilement|en\s+\d+)",
    r"rendements?\s+garantis?",
    r"gains?\s+garantis?",
    r"profits?\s+garantis?",
    r"b[ée]n[ée]fices?\s+garantis?",
    r"je\s+(vous\s+)?garantis",
    r"garanti[e]?\s+de\s+gain",
    r"doubl(er|ez)\s+(votre|ton|son)\s+capital",
    r"multipli(er|ez)\s+(votre|ton|son)\s+(capital|argent)",
    r"100\s*%\s+de\s+(r[ée]ussite|gagnant)",
    r"toujours\s+gagnant",
    r"ne\s+(jamais|plus)\s+perdre",
    r"ne\s+perd(ez|s)\s+(jamais|plus)",
    r"placement\s+sans\s+risque",
    r"valeur\s+s[ûu]re",
    r"trade\s+s[ûu]r",
    r"signal\s+s[ûu]r",
    r"argent\s+rapide",
]

# Promesses chiffrées de profit, ex. « +50% par mois », « x3 en 1 semaine ».
PROFIT_CHIFFRE = [
    r"\+?\s*\d{2,}\s*%\s*(par|/|en)\s*(jour|semaine|mois|an)",
    r"x\s?\d+\s+(en|par)\s+\d+",
    r"\d+\s*€?\s+en\s+\d+\s+(jours?|semaines?|heures?)",
]

# --- 2. Détection du contexte (pour savoir quels garde-fous exiger) --------
CONTEXTE_TRADING = [
    r"\btrading\b", r"\btrade(r|s)?\b", r"\bforex\b", r"\bcfd\b", r"\bbroker\b",
    r"\bmarch[ée]s?\b", r"\bscalping\b", r"\bcapital\b", r"\blevier\b",
    r"\bposition\b", r"\binvestir\b", r"\binvestissement\b", r"\btrad(é|er)\b",
]
CONTEXTE_BROKER = [
    r"\bfxlift\b", r"\btelegram\b", r"\bd[ée]p[ôo]t\b", r"\bbroker\s+partenaire\b",
    r"ouvr(ir|ez)\s+un\s+compte", r"rejoin(s|dre|t)\s+(le|notre)\s+(canal|telegram)",
    r"lien\s+en\s+(bio|commentaire)",
]

# --- 3. Garde-fous attendus ------------------------------------------------
# Avertissement de risque (§6.2) : on cherche les mots-clés essentiels.
RISK_MARKERS = [
    r"risque\s+de\s+perte", r"perte\s+en\s+capital",
    r"comptes?\s+(particuliers?|de\s+d[ée]tail)\s+perdent",
]
# Disclosure d'affiliation (§6.3).
DISCLOSURE_MARKERS = [
    r"#ad\b", r"partenariat", r"partenaire\s+r[ée]mun[ée]r[ée]",
    r"r[ée]mun[ée]r[ée]", r"affili(ation|[ée])",
]
# Conseil personnalisé interdit (§6.4) → WARN (à relire par un humain).
CONSEIL_PERSO = [
    r"ach[èe]te[zr]?\s+\w+\s+(maintenant|aujourd)", r"vend[zs]?\s+\w+\s+maintenant",
    r"je\s+(te|vous)\s+conseille\s+d['e]\s*(acheter|vendre|investir)",
    r"mets?\s+tout\s+(ton|votre)\s+(argent|capital)",
]


def _trouve(patterns, texte):
    """Renvoie la liste des motifs trouvés (insensible à la casse/accents légers)."""
    res = []
    for p in patterns:
        if re.search(p, texte, flags=re.IGNORECASE):
            res.append(p)
    return res


@dataclass
class Verdict:
    statut: str = "OK"                 # OK | WARN | BLOCK
    raisons: list = field(default_factory=list)

    def _degrade(self, niveau: str, raison: str):
        ordre = {"OK": 0, "WARN": 1, "BLOCK": 2}
        if ordre[niveau] > ordre[self.statut]:
            self.statut = niveau
        self.raisons.append(f"[{niveau}] {raison}")


def verifier(texte: str) -> Verdict:
    """Analyse un texte brut (LinkedIn complet ou thread X concaténé)."""
    v = Verdict()
    bas = texte.lower()

    # 1. Mots/expressions interdits → BLOCK
    for p in _trouve(INTERDITS, bas):
        v._degrade("BLOCK", f"Expression interdite (promesse/garantie) : /{p}/")
    for p in _trouve(PROFIT_CHIFFRE, bas):
        v._degrade("BLOCK", f"Promesse chiffrée de profit : /{p}/")

    parle_trading = bool(_trouve(CONTEXTE_TRADING, bas))
    pousse_broker = bool(_trouve(CONTEXTE_BROKER, bas))

    # 2. Avertissement de risque requis dès qu'on parle trading (§6.2)
    if parle_trading and not _trouve(RISK_MARKERS, bas):
        v._degrade("BLOCK", "Parle de trading mais AUCUN avertissement de risque.")

    # 3. Disclosure d'affiliation requise si on pousse vers le broker (§6.3)
    if pousse_broker and not _trouve(DISCLOSURE_MARKERS, bas):
        v._degrade("BLOCK", "Pousse vers FxLift/Telegram sans disclosure (#ad/partenariat).")

    # 4. Conseil personnalisé → WARN (à relire)
    for p in _trouve(CONSEIL_PERSO, bas):
        v._degrade("WARN", f"Tournure pouvant ressembler à un conseil personnalisé : /{p}/")

    return v


def verifier_post(post: dict) -> dict:
    """Vérifie les 2 versions d'un post (dict issu du moteur).

    Renvoie le post enrichi d'un bloc `conformite` :
        { "linkedin": Verdict, "x": Verdict, "statut": pire des deux }
    """
    txt_li = post["linkedin"]["texte"] + " " + " ".join(post["linkedin"].get("hashtags", []))
    txt_x = " ".join(post["x"]["thread"]) + " " + " ".join(post["x"].get("hashtags", []))
    v_li = verifier(txt_li)
    v_x = verifier(txt_x)

    ordre = {"OK": 0, "WARN": 1, "BLOCK": 2}
    pire = max([v_li.statut, v_x.statut], key=lambda s: ordre[s])

    post["conformite"] = {
        "statut": pire,
        "linkedin": {"statut": v_li.statut, "raisons": v_li.raisons},
        "x": {"statut": v_x.statut, "raisons": v_x.raisons},
    }
    return post


# Petit auto-test : `python posts/compliance.py`
if __name__ == "__main__":
    exemples = {
        "Promesse interdite": "Gagne sans risque, devenez riche rapidement grâce au trading !",
        "Trading sans warning": "Le scalping contrarien sur le forex, voici ma méthode.",
        "Conforme": (
            "Le scalping demande de la discipline. La gestion du risque d'abord. "
            "⚠️ Le trading de CFD/forex comporte un risque de perte en capital. "
            "La majorité des comptes particuliers perdent de l'argent."
        ),
    }
    for nom, txt in exemples.items():
        v = verifier(txt)
        print(f"\n{nom} → {v.statut}")
        for r in v.raisons:
            print("   ", r)
