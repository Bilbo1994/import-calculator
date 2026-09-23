"""
Petite couche SQLite pour stocker les prix saisis manuellement
(fret maritime, prix véhicules) affichés sur la page /marche.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "marche.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fret_prix (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            prix_usd REAL NOT NULL,
            note TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vehicule_prix (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            modele TEXT NOT NULL,
            prix_dzd REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def ajouter_fret(date_str, prix_usd, note):
    conn = get_db()
    conn.execute(
        "INSERT INTO fret_prix (date, prix_usd, note) VALUES (?, ?, ?)",
        (date_str, prix_usd, note),
    )
    conn.commit()
    conn.close()


def lister_fret():
    conn = get_db()
    rows = conn.execute(
        "SELECT date, prix_usd, note FROM fret_prix ORDER BY date ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def ajouter_vehicule(date_str, modele, prix_dzd):
    conn = get_db()
    conn.execute(
        "INSERT INTO vehicule_prix (date, modele, prix_dzd) VALUES (?, ?, ?)",
        (date_str, modele, prix_dzd),
    )
    conn.commit()
    conn.close()


def lister_vehicules():
    conn = get_db()
    rows = conn.execute(
        "SELECT date, modele, prix_dzd FROM vehicule_prix ORDER BY date ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
