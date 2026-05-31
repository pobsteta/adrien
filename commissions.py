"""
Rapport d'attribution — compte les leads par source et par VA.
Base de calcul des 20 % de commission des VA.

Lance : python commissions.py
"""

import sqlite3
from collections import Counter

from config import DB_PATH


def report() -> None:
    con = sqlite3.connect(DB_PATH)
    rows = con.execute("SELECT declared_src, va_name FROM leads").fetchall()
    con.close()

    sources = Counter()
    par_va = Counter()
    for declared, va_name in rows:
        sources[declared or "inconnu"] += 1
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
