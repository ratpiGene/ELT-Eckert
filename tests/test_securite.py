"""
C4.4.1 — Tests de sécurité du cahier de recette.

Trois familles, toutes reliées à une ligne du cahier de recette
(livrables/C4-4-1_cahier_recette.md) :

  SEC-01  non-exposition des secrets dans le dépôt (toujours exécuté) ;
  SEC-02  moindre privilège : le rôle de lecture ne peut pas écrire
          (exécuté si l'entrepôt est joignable, ignoré sinon) ;
  SEC-03  cloisonnement : le rôle de lecture n'accède pas aux couches techniques.

Les tests SEC-02/03 ont besoin d'un PostgreSQL joignable avec les rôles
applicatifs créés (docker compose up). Ils sont ignorés proprement sinon, pour
que la suite reste verte en intégration continue sans base.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]


# --- SEC-01 : non-exposition des secrets ------------------------------------
def test_aucun_env_versionne() -> None:
    """Aucun fichier .env ne doit être suivi par git."""
    suivis = subprocess.run(
        ["git", "ls-files"], cwd=RACINE, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    fautifs = [f for f in suivis if Path(f).name == ".env" or f.endswith("/.env")]
    assert not fautifs, f"Fichier(s) de secrets versionné(s) : {fautifs}"


def test_gitignore_couvre_les_secrets() -> None:
    contenu = (RACINE / ".gitignore").read_text(encoding="utf-8")
    for motif in (".env", "*.pem", "*.key"):
        assert motif in contenu, f"Le motif {motif!r} devrait être ignoré par git"


def test_pas_de_mot_de_passe_en_dur_dans_le_code() -> None:
    """Le code applicatif lit les secrets dans l'environnement, jamais en clair.

    On tolère les valeurs de repli explicites 'changeme' (visiblement factices)
    et on refuse toute affectation d'un mot de passe d'apparence réelle.
    """
    import re

    interdit = re.compile(
        r"(password|mot_de_passe)\s*=\s*[\"'](?!changeme|\s*$)[^\"']{6,}[\"']", re.I
    )
    for fichier in (RACINE / "src").rglob("*.py"):
        texte = fichier.read_text(encoding="utf-8")
        for numero, ligne in enumerate(texte.splitlines(), 1):
            if "os.environ" in ligne or "getenv" in ligne or "_env(" in ligne:
                continue  # lecture depuis l'environnement : conforme
            assert not interdit.search(ligne), f"Secret potentiel en dur : {fichier}:{numero}"


# --- Pré-requis des tests base -------------------------------------------
def _dsn_reader() -> str | None:
    mdp = os.environ.get("ELT_READER_PASSWORD")
    if not mdp:
        return None
    hote = os.environ.get("PG_HOST", "localhost")
    port = os.environ.get("PG_PORT", "5432")
    return f"postgresql://elt_reader:{mdp}@{hote}:{port}/eckert"


def _connexion_reader():
    dsn = _dsn_reader()
    if not dsn:
        pytest.skip("ELT_READER_PASSWORD absent : test base ignoré (entrepôt non configuré)")
    try:
        import psycopg
    except ImportError:  # pragma: no cover
        pytest.skip("psycopg indisponible")
    try:
        return psycopg.connect(dsn, connect_timeout=3)
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"entrepôt injoignable : {exc}")


# --- SEC-02 : moindre privilège — la lecture ne peut pas écrire --------------
def test_reader_ne_peut_pas_ecrire_en_gold() -> None:
    import psycopg

    with (
        _connexion_reader() as connexion,
        connexion.cursor() as curseur,
        pytest.raises(psycopg.errors.InsufficientPrivilege),
    ):
        curseur.execute(
            "INSERT INTO gold.contrat_desherence "
            "(contrat_id, adherent_id, date_deces, jours_depuis_deces, niveau_confiance, run_id) "
            "VALUES (-1, -1, current_date, 0, 'CERTAIN', 'test-securite')"
        )


# --- SEC-03 : cloisonnement — pas d'accès aux couches techniques -------------
def test_reader_ne_voit_pas_le_bronze() -> None:
    import psycopg

    with (
        _connexion_reader() as connexion,
        connexion.cursor() as curseur,
        pytest.raises(psycopg.errors.InsufficientPrivilege),
    ):
        curseur.execute("SELECT count(*) FROM bronze.deces_brut")
