"""C4.2.2 — Chargement bronze : la ligne source telle que reçue, plus sa traçabilité."""

from __future__ import annotations

import logging
from pathlib import Path

from eckert.config import CONFIG

logger = logging.getLogger(__name__)

TAILLE_LOT = 20_000


def charger(fichier: Path, run_id: str, encodage: str = "utf-8") -> int:
    """Charge le fichier en bronze par COPY, retourne le nombre de lignes."""
    import psycopg

    total = 0
    with psycopg.connect(CONFIG.pg_dsn) as connexion:
        with (
            connexion.cursor() as curseur,
            fichier.open("r", encoding=encodage, errors="replace") as flux,
            curseur.copy(
                "COPY bronze.deces_brut (ligne_source, fichier_source, ligne_numero, run_id) "
                "FROM STDIN"
            ) as copie,
        ):
            for numero, ligne in enumerate(flux, start=1):
                ligne = ligne.rstrip("\n").rstrip("\r")
                if not ligne.strip():
                    continue
                echappee = ligne.replace("\\", "\\\\").replace("\t", " ")
                copie.write(f"{echappee}\t{fichier.name}\t{numero}\t{run_id}\n")
                total += 1
        connexion.commit()

    logger.info("Bronze : %d lignes chargées depuis %s", total, fichier.name)
    return total
