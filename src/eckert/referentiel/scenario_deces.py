"""
Génération d'un fichier décès de DÉMONSTRATION, au format INSEE (largeur fixe
176), avec un recouvrement contrôlé du référentiel synthétique.

Pourquoi ce fichier ? Le vrai fichier INSEE sert à prouver l'ingestion, la
validation par le contenu et la volumétrie (justification du distribué). Mais ses
identités ne recoupent pas le référentiel synthétique : le rapprochement ne
produirait rien de démontrable. Ce générateur fabrique donc un fichier décès
*synthétique* qui partage, de façon maîtrisée, une partie des identités du
référentiel — afin que gold.contrat_desherence contienne des cas aux trois
niveaux de confiance (CERTAIN, PROBABLE, A_VERIFIER).

C'est un jeu de démonstration, clairement identifié comme tel. Aucune donnée
réelle n'y figure.

    PYTHONPATH=src python -m eckert.referentiel.scenario_deces \
        --adherents data/referentiel/adherents.csv \
        --sortie data/bronze/demo/deces-demo.txt
"""

from __future__ import annotations

import argparse
import csv
import logging
import random
from datetime import date, timedelta
from pathlib import Path

from faker import Faker

logger = logging.getLogger(__name__)

# Réplique de la spécification (cf. eckert.validation.contract.CHAMPS).
_LARGEURS = [
    ("nom_prenoms", 80),
    ("sexe", 1),
    ("date_naissance", 8),
    ("code_lieu_naissance", 5),
    ("commune_naissance", 30),
    ("pays_naissance", 30),
    ("date_deces", 8),
    ("code_lieu_deces", 5),
    ("numero_acte_deces", 9),
]


def _ligne(champs: dict[str, str]) -> str:
    return "".join(str(champs.get(nom, "")).ljust(largeur)[:largeur] for nom, largeur in _LARGEURS)


def _aaaammjj(valeur_iso: str) -> str:
    return valeur_iso.replace("-", "")


def generer(
    chemin_adherents: Path,
    sortie: Path,
    taux_deces: float = 0.15,
    part_certain: float = 0.7,
    nb_homonymes: int = 40,
    nb_bruit: int = 1200,
    graine: int = 7,
) -> dict[str, int]:
    """Écrit le fichier décès de démonstration. Retourne le décompte par cas."""
    random.seed(graine)
    faker = Faker("fr_FR")
    Faker.seed(graine)

    with chemin_adherents.open("r", encoding="utf-8") as flux:
        adherents = list(csv.DictReader(flux, delimiter=";"))

    random.shuffle(adherents)
    nb_deces = int(len(adherents) * taux_deces)
    decedes = adherents[:nb_deces]
    # Les homonymes sont pris parmi des adhérents NON décédés, pour rester en
    # « à vérifier » (le job Spark écarte ceux déjà rapprochés avec certitude).
    candidats_homonymes = adherents[nb_deces : nb_deces + nb_homonymes]

    aujourdhui = date.today()

    def date_deces_recente() -> str:
        jour = aujourdhui - timedelta(days=random.randint(30, 1500))
        return jour.strftime("%Y%m%d")

    compte = {"CERTAIN": 0, "PROBABLE": 0, "A_VERIFIER": 0, "bruit": 0}
    lignes: list[str] = []

    for adherent in decedes:
        certain = random.random() < part_certain
        lignes.append(
            _ligne(
                {
                    "nom_prenoms": f"{adherent['nom']}*{adherent['prenoms']}/",
                    "sexe": adherent["sexe"],
                    "date_naissance": _aaaammjj(adherent["date_naissance"]),
                    # CERTAIN : le lieu de naissance concorde ; sinon divergence -> PROBABLE
                    "code_lieu_naissance": adherent["code_insee_naiss"] if certain else "99999",
                    "commune_naissance": faker.city(),
                    "pays_naissance": "FRANCE",
                    "date_deces": date_deces_recente(),
                    "code_lieu_deces": faker.postcode()[:5],
                    "numero_acte_deces": str(random.randint(1, 999999999)).zfill(9),
                }
            )
        )
        compte["CERTAIN" if certain else "PROBABLE"] += 1

    for adherent in candidats_homonymes:
        autre_prenom = (
            faker.first_name_male() if adherent["sexe"] == "1" else faker.first_name_female()
        )
        if autre_prenom.upper() == adherent["prenoms"].upper():
            autre_prenom += "BIS"
        lignes.append(
            _ligne(
                {
                    "nom_prenoms": f"{adherent['nom']}*{autre_prenom}/",
                    "sexe": adherent["sexe"],
                    "date_naissance": _aaaammjj(adherent["date_naissance"]),
                    "code_lieu_naissance": adherent["code_insee_naiss"],
                    "commune_naissance": faker.city(),
                    "pays_naissance": "FRANCE",
                    "date_deces": date_deces_recente(),
                    "code_lieu_deces": faker.postcode()[:5],
                    "numero_acte_deces": str(random.randint(1, 999999999)).zfill(9),
                }
            )
        )
        compte["A_VERIFIER"] += 1

    for _ in range(nb_bruit):
        sexe = random.choice(["1", "2"])
        prenom = faker.first_name_male() if sexe == "1" else faker.first_name_female()
        naissance = aujourdhui - timedelta(days=random.randint(25 * 365, 100 * 365))
        lignes.append(
            _ligne(
                {
                    "nom_prenoms": f"{faker.last_name().upper()}*{prenom}/",
                    "sexe": sexe,
                    "date_naissance": naissance.strftime("%Y%m%d"),
                    "code_lieu_naissance": faker.postcode()[:5],
                    "commune_naissance": faker.city(),
                    "pays_naissance": "FRANCE",
                    "date_deces": date_deces_recente(),
                    "code_lieu_deces": faker.postcode()[:5],
                    "numero_acte_deces": str(random.randint(1, 999999999)).zfill(9),
                }
            )
        )
        compte["bruit"] += 1

    random.shuffle(lignes)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text("\n".join(lignes) + "\n", encoding="utf-8")

    logger.info(
        "Fichier décès de démonstration écrit : %s (%d lignes — %s)",
        sortie,
        len(lignes),
        ", ".join(f"{k}={v}" for k, v in compte.items()),
    )
    return compte


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parseur = argparse.ArgumentParser(description="Fichier décès de démonstration (recouvrement)")
    parseur.add_argument("--adherents", type=Path, default=Path("data/referentiel/adherents.csv"))
    parseur.add_argument("--sortie", type=Path, default=Path("data/bronze/demo/deces-demo.txt"))
    parseur.add_argument("--taux-deces", type=float, default=0.15)
    parseur.add_argument("--bruit", type=int, default=1200)
    parseur.add_argument("--graine", type=int, default=7)
    args = parseur.parse_args()
    generer(
        args.adherents,
        args.sortie,
        taux_deces=args.taux_deces,
        nb_bruit=args.bruit,
        graine=args.graine,
    )


if __name__ == "__main__":
    main()
