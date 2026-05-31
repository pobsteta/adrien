"""Stockage des leads pour l'attribution des commissions."""

import sqlite3
from datetime import datetime, timezone

from config import DB_PATH


def init_db() -> None:
    con = sqlite3.connect(DB_PATH)
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            user_id        INTEGER PRIMARY KEY,
            username       TEXT,
            first_name     TEXT,
            declared_src   TEXT,   -- source déclarée : founders / elisa / va / autre
            va_name        TEXT,   -- nom du VA si applicable
            created_at     TEXT
        )
        """
    )
    con.commit()
    con.close()


def upsert_lead(user, declared_src=None, va_name=None) -> None:
    con = sqlite3.connect(DB_PATH)
    now = datetime.now(timezone.utc).isoformat()
    con.execute(
        """
        INSERT INTO leads (user_id, username, first_name, declared_src,
                           va_name, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username     = excluded.username,
            first_name   = excluded.first_name,
            declared_src = COALESCE(excluded.declared_src, leads.declared_src),
            va_name      = COALESCE(excluded.va_name,      leads.va_name)
        """,
        (user.id, user.username, user.first_name,
         declared_src, va_name, now),
    )
    con.commit()
    con.close()
