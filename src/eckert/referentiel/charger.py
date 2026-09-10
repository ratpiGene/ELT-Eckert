"""
Chargement du référentiel synthétique dans silver.adherent / silver.contrat.

Le référentiel est produit par `eckert.referentiel.generate` (Faker) ; il est
ici chargé en base par COPY, en repartant d'une table vide (le référentiel est
un état, pas un flux). Aucune donnée réelle n'est concernée.

    PYTHONPATH=src python -m eckert.referentiel.charger \
        --adherents data/referentiel/adherents.csv \
        --contrats  data/referentiel/contrats.csv
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from eckert.config import CONFIG

logger = logging.getLogger(__name__)


def charger(chemin_adherents: Path, chemin_contrats: Path) -> tuple[int, int]:
    import psycopg

    with psycopg.connect(CONFIG.pg_dsn) as connexion, connexion.cursor() as curseur:
        # Le référentiel est un état complet : on repart d'une base vide.
        # DELETE (et non TRUNCATE) car le rôle elt_writer applique le moindre
        # privilège : il dispose du DELETE, pas du TRUNCATE réservé au propriétaire.
        # L'ordre respecte la clé étrangère contrat -> adherent.
        curseur.execute("DELETE FROM silver.contrat;")
        curseur.execute("DELETE FROM silver.adherent;")

        with (
            chemin_adherents.open("r", encoding="utf-8") as f_adh,
            curseur.copy(
                "COPY silver.adherent "
                "(adherent_id, nom, prenoms, sexe, date_naissance, code_insee_naiss, "
                "cle_rapprochement, statut) "
                "FROM STDIN WITH (FORMAT csv, HEADER true, DELIMITER ';')"
            ) as copie,
        ):
            while bloc := f_adh.read(1 << 20):
                copie.write(bloc)
        nb_adherents = curseur.rowcount

        with (
            chemin_contrats.open("r", encoding="utf-8") as f_ctr,
            curseur.copy(
                "COPY silver.contrat "
                "(contrat_id, adherent_id, date_effet, date_fin, capital_garanti, statut) "
                "FROM STDIN WITH (FORMAT csv, HEADER true, DELIMITER ';', NULL '')"
            ) as copie,
        ):
            while bloc := f_ctr.read(1 << 20):
                copie.write(bloc)
        nb_contrats = curseur.rowcount

        connexion.commit()

    logger.info("Référentiel chargé : %d adhérents, %d contrats", nb_adherents, nb_contrats)
    return nb_adherents, nb_contrats


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parseur = argparse.ArgumentParser(description="Charge le référentiel synthétique en silver")
    parseur.add_argument("--adherents", type=Path, default=Path("data/referentiel/adherents.csv"))
    parseur.add_argument("--contrats", type=Path, default=Path("data/referentiel/contrats.csv"))
    args = parseur.parse_args()
    charger(args.adherents, args.contrats)


if __name__ == "__main__":
    main()
