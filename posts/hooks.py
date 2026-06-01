"""Banque de hooks et d'angles de storytelling (§7).

Ces éléments servent de GRAINES d'inspiration injectées dans le prompt : Claude
doit les reformuler, jamais les recopier tels quels. Le but est de varier les
accroches et d'éviter que les posts se ressemblent (§3, §6).

Ajoute librement tes propres hooks au fil du temps : c'est une simple liste.
"""

import random

# --- Hooks LinkedIn : 1re ligne forte, avant le « …voir plus » -------------
HOOKS_LINKEDIN = [
    "Pendant 2 ans, j'ai perdu de l'argent sur les marchés. Voici ce que personne ne m'avait dit.",
    "On m'a dit que je n'étais « pas fait pour ça ». Aujourd'hui, je vis de ma méthode.",
    "Mon plus gros progrès en trading n'a rien à voir avec une stratégie.",
    "La vérité que les comptes Instagram de trading ne vous montreront jamais.",
    "J'ai failli tout arrêter. Cette décision a tout changé.",
    "Le jour où j'ai arrêté de copier les autres, mes résultats ont changé.",
    "Personne ne vous le dit, mais la discipline pèse plus lourd que la stratégie.",
    "Ce que mes 2 premières années de pertes m'ont vraiment appris.",
    "Changer de vie ne demande pas du courage tous les jours. Juste une décision, répétée.",
    "L'erreur de débutant qui m'a coûté le plus cher (et comment l'éviter).",
]

# --- Hooks X : 1er tweet qui accroche seul, court et direct ----------------
HOOKS_X = [
    "2 ans de pertes avant de devenir rentable. Le thread que j'aurais aimé lire au début 🧵",
    "Ton problème en trading n'est pas ta stratégie. C'est ça 👇",
    "Petit rappel : la majorité des débutants échouent pour la même raison.",
    "J'ai arrêté de chercher le « bon » setup. Voilà ce qui a changé.",
    "La gestion du risque expliquée simplement (en 5 tweets) 🧵",
    "Ce que j'aurais dit à mon moi d'il y a 5 ans.",
    "Le piège n°1 du débutant n'est pas technique. Il est mental.",
    "Tu veux changer de vie ? Commence par arrêter de faire ça.",
]

# --- Angles de storytelling tirés du parcours d'Adrien (§3.2) --------------
ANGLES_STORYTELLING = [
    "Les 2 premières années de pertes : à quoi ressemblait concrètement le quotidien.",
    "Le moment précis du « déclic » et ce qui l'a déclenché.",
    "La fois où il a voulu tout arrêter — et pourquoi il a continué.",
    "Une erreur de débutant marquante et la leçon durable qu'il en a tirée.",
    "La découverte du scalping contrarien : pourquoi cette méthode lui a parlé.",
    "Ce que sa famille/ses proches pensaient au début, et comment il l'a vécu.",
    "La différence entre l'Adrien d'avant (impatient) et celui d'aujourd'hui (discipliné).",
    "Le piège des promesses de gains rapides : comment il a failli tomber dedans.",
    "Pourquoi il documente publiquement, même les périodes difficiles (transparence).",
    "La routine ou l'habitude qui a le plus changé ses résultats.",
]


def pick(seq, used=None):
    """Tire un élément au hasard en évitant ceux déjà utilisés dans la session."""
    used = used or set()
    dispo = [x for x in seq if x not in used] or list(seq)
    choix = random.choice(dispo)
    used.add(choix)
    return choix
