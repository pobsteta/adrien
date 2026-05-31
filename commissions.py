"""
Rapport d'attribution — compte les leads par source et par VA.
Sert de base pour calculer les 20 % de commission des VA.

Lance : python commissions.py
"""

import sqlite3
from collections import Counter

DB_PATH = "attribution.db"


def report() -> None:
    con = sqlite3.connect(DB_PATH)
    rows = con.execute(
        "SELECT declared_src, deeplink_src, va_name FROM leads"
    ).fetchall()
    con.close()

    sources = Counter()
    par_va = Counter()
    for declared, deeplink, va_name in rows:
        # On privilégie la source déclarée, sinon celle du lien de parrainage
        src = declared or deeplink or "inconnu"
        sources[src] += 1
        if va_name:
            par_va[va_name] += 1

    print(f"Total leads : {len(rows)}\n")
    print("Par source :")
    for src, n in sources.most_common():
        print(f"  {src:12} {n}")

    if par_va:
        print("\nPar ambassadeur (VA) — base commission 20 % :")
        for name, n in par_va.most_common():
            print(f"  {name:12} {n} leads")


if __name__ == "__main__":
    report()
