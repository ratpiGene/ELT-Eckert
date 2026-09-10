"""
C4.4.1 — Tests structurels du contrat de données.

Chaque test correspond à une ligne du cahier de recette
(livrables/C4-4-1_cahier_recette.md).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from eckert.validation.contract import (
    LIGNES_MINIMUM,
    LONGUEUR_LIGNE,
    controler_metadonnees,
    valider_fichier,
)


def _ligne(
    nom: str = "DUPONT*JEAN/",
    sexe: str = "1",
    naissance: str = "19450612",
    deces: str = "20240115",
) -> str:
    return (
        nom.ljust(80)
        + sexe
        + naissance
        + "33063"
        + "BORDEAUX".ljust(30)
        + "FRANCE".ljust(30)
        + deces
        + "33063"
        + "123456789"
    )


def _ecrire(tmp_path: Path, lignes: list[str], nom: str = "deces-test.txt") -> Path:
    chemin = tmp_path / nom
    chemin.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    return chemin


# --- REC-01 : nominal -------------------------------------------------------
def test_fichier_nominal_est_conforme(tmp_path: Path) -> None:
    fichier = _ecrire(tmp_path, [_ligne()] * (LIGNES_MINIMUM + 10))
    rapport = valider_fichier(fichier)
    assert rapport.conforme
    assert rapport.lignes_rejetees == 0
    assert rapport.lignes_conformes == LIGNES_MINIMUM + 10


def test_longueur_de_ligne_conforme_a_la_specification() -> None:
    assert len(_ligne()) == LONGUEUR_LIGNE


# --- REC-02 : fichier vide --------------------------------------------------
def test_fichier_vide_est_bloquant(tmp_path: Path) -> None:
    chemin = tmp_path / "vide.txt"
    chemin.write_text("", encoding="utf-8")
    rapport = valider_fichier(chemin)
    assert not rapport.conforme
    assert "fichier vide" in rapport.bloquant


def test_fichier_absent_est_bloquant(tmp_path: Path) -> None:
    rapport = valider_fichier(tmp_path / "inexistant.txt")
    assert not rapport.conforme


# --- REC-03 : volumétrie anormale -------------------------------------------
def test_volumetrie_trop_basse_est_bloquante(tmp_path: Path) -> None:
    fichier = _ecrire(tmp_path, [_ligne()] * 10)
    rapport = valider_fichier(fichier)
    assert not rapport.conforme
    assert any("volumétrie" in motif for motif in rapport.bloquant)


# --- REC-04 : lignes malformées ---------------------------------------------
def test_ligne_tronquee_est_rejetee(tmp_path: Path) -> None:
    lignes = [_ligne()] * LIGNES_MINIMUM + ["TROP COURT"]
    rapport = valider_fichier(_ecrire(tmp_path, lignes))
    assert rapport.lignes_rejetees == 1
    assert rapport.erreurs["longueur_insuffisante"] == 1
    assert rapport.conforme  # une ligne sur 1001 reste sous le seuil


def test_date_deces_impossible_est_rejetee(tmp_path: Path) -> None:
    lignes = [_ligne()] * LIGNES_MINIMUM + [_ligne(deces="20249999")]
    rapport = valider_fichier(_ecrire(tmp_path, lignes))
    assert rapport.erreurs.get("date_deces_invalide") == 1


def test_jour_inconnu_reste_accepte(tmp_path: Path) -> None:
    """Un jour à 00 signifie « inconnu » dans la spécification, pas une erreur."""
    lignes = [_ligne(deces="20240100")] * LIGNES_MINIMUM
    rapport = valider_fichier(_ecrire(tmp_path, lignes))
    assert rapport.lignes_rejetees == 0


def test_sexe_invalide_est_rejete(tmp_path: Path) -> None:
    lignes = [_ligne()] * LIGNES_MINIMUM + [_ligne(sexe="9")]
    rapport = valider_fichier(_ecrire(tmp_path, lignes))
    assert rapport.erreurs.get("sexe_invalide") == 1


# --- REC-05 : seuil de rejet ------------------------------------------------
def test_taux_de_rejet_au_dessus_du_seuil_est_bloquant(tmp_path: Path) -> None:
    bonnes = [_ligne()] * LIGNES_MINIMUM
    mauvaises = ["X" * 10] * 200  # 200 / 1200 ≈ 17 %
    rapport = valider_fichier(_ecrire(tmp_path, bonnes + mauvaises))
    assert not rapport.conforme
    assert any("taux de rejet" in motif for motif in rapport.bloquant)


# --- REC-06 : NON-RÉGRESSION DE L'INCIDENT ----------------------------------
# Le fichier est valide, mais le producteur ne publie plus ses métadonnées.
# Comportement attendu : ALERTE, et le traitement continue.
def test_metadonnees_absentes_ne_bloquent_pas(tmp_path: Path) -> None:
    fichier = _ecrire(tmp_path, [_ligne()] * (LIGNES_MINIMUM + 1))
    rapport = valider_fichier(fichier)
    alertes = controler_metadonnees(ecarts=[], metadonnees_absentes=["checksum", "filesize"])

    assert rapport.conforme, "un fichier sain doit rester traité même sans métadonnées"
    assert len(alertes) == 1
    assert "ne publie plus les métadonnées" in alertes[0]


def test_ecart_de_taille_declare_leve_une_alerte_sans_bloquer() -> None:
    alertes = controler_metadonnees(
        ecarts=["taille déclarée 100 != taille réelle 120"], metadonnees_absentes=[]
    )
    assert len(alertes) == 1
    assert "Écart déclaré/réel" in alertes[0]


@pytest.mark.parametrize("encodage", ["utf-8", "latin-1"])
def test_encodage_inattendu_ne_fait_pas_planter(tmp_path: Path, encodage: str) -> None:
    chemin = tmp_path / "encodage.txt"
    lignes = [_ligne(nom="LE GOFF*ANDRÉ/")] * LIGNES_MINIMUM
    chemin.write_text("\n".join(lignes) + "\n", encoding=encodage)
    rapport = valider_fichier(chemin)
    assert rapport.lignes_lues == LIGNES_MINIMUM
