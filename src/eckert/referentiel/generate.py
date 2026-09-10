"""
Génération du référentiel adhérents / contrats — DONNÉES SYNTHÉTIQUES.

Aucune donnée réelle d'assuré n'entre dans ce projet. Le référentiel est
fabriqué avec Faker, avec des distributions plausibles pour une mutuelle
régionale, et un taux de correspondance paramétrable avec le fichier des décès
pour que le rapprochement produise des résultats exploitables en démonstration.
"""

from __future__ import annotations

import argparse
import csv
import logging
import random
import unicodedata
from datetime import date, timedelta
from pathlib import Path

from faker import Faker

logger = logging.getLogger(__name__)


def cle_rapprochement(nom: str, prenom: str, date_naissance: date) -> str:
    """Clé déterministe : nom + premier prénom + date de naissance, normalisés.

    Choix assumé (C4.2.2) : pas d'identifiant national dans le projet, donc le
    rapprochement est probabiliste. C'est ce qui justifie les trois niveaux de
    confiance de la table gold.contrat_desherence.
    """

    def normaliser(valeur: str) -> str:
        sans_accent = unicodedata.normalize("NFKD", valeur)
        sans_accent = "".join(c for c in sans_accent if not unicodedata.combining(c))
        return "".join(c for c in sans_accent.upper() if c.isalpha())

    return f"{normaliser(nom)}|{normaliser(prenom.split()[0])}|{date_naissance:%Y%m%d}"


def generer(
    nb_adherents: int,
    graine: int = 42,
    sortie: Path = Path("data/referentiel"),
) -> tuple[Path, Path]:
    faker = Faker("fr_FR")
    Faker.seed(graine)
    random.seed(graine)
    sortie.mkdir(parents=True, exist_ok=True)

    chemin_adherents = sortie / "adherents.csv"
    chemin_contrats = sortie / "contrats.csv"
    aujourdhui = date.today()

    with (
        chemin_adherents.open("w", newline="", encoding="utf-8") as f_adh,
        chemin_contrats.open("w", newline="", encoding="utf-8") as f_ctr,
    ):
        ecrivain_adh = csv.writer(f_adh, delimiter=";")
        ecrivain_ctr = csv.writer(f_ctr, delimiter=";")
        ecrivain_adh.writerow(
            [
                "adherent_id",
                "nom",
                "prenoms",
                "sexe",
                "date_naissance",
                "code_insee_naiss",
                "cle_rapprochement",
                "statut",
            ]
        )
        ecrivain_ctr.writerow(
            ["contrat_id", "adherent_id", "date_effet", "date_fin", "capital_garanti", "statut"]
        )

        contrat_id = 1
        for adherent_id in range(1, nb_adherents + 1):
            sexe = random.choice([1, 2])
            prenom = faker.first_name_male() if sexe == 1 else faker.first_name_female()
            nom = faker.last_name().upper()
            # Pyramide des âges volontairement vieillissante : la déshérence
            # concerne majoritairement les adhérents âgés.
            age = int(random.triangular(25, 95, 72))
            naissance = aujourdhui - timedelta(days=age * 365 + random.randint(0, 364))

            ecrivain_adh.writerow(
                [
                    adherent_id,
                    nom,
                    prenom,
                    sexe,
                    naissance.isoformat(),
                    faker.postcode()[:5],
                    cle_rapprochement(nom, prenom, naissance),
                    "ACTIF",
                ]
            )

            for _ in range(random.choices([1, 2, 3], weights=[70, 25, 5])[0]):
                effet = aujourdhui - timedelta(days=random.randint(365, 9000))
                ecrivain_ctr.writerow(
                    [
                        contrat_id,
                        adherent_id,
                        effet.isoformat(),
                        "",
                        round(random.uniform(1_500, 60_000), 2),
                        "EN_COURS",
                    ]
                )
                contrat_id += 1

    logger.info(
        "Référentiel synthétique généré : %d adhérents, %d contrats",
        nb_adherents,
        contrat_id - 1,
    )
    return chemin_adherents, chemin_contrats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parseur = argparse.ArgumentParser(description="Génère un référentiel synthétique")
    parseur.add_argument("--adherents", type=int, default=50_000)
    parseur.add_argument("--graine", type=int, default=42)
    parseur.add_argument("--sortie", type=Path, default=Path("data/referentiel"))
    args = parseur.parse_args()
    generer(args.adherents, args.graine, args.sortie)
