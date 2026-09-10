"""
C4.2.2 — Promotion bronze → silver, en SQL, au fil de l'eau.

C'est la méthode « pipeline temps réel (SQL) » de la grille : le découpage à
largeur fixe, le typage et la déduplication sont poussés dans le moteur, au
plus près de la donnée, sans la faire transiter par l'application.
"""

from __future__ import annotations

import logging

from eckert.config import CONFIG
from eckert.validation.contract import CHAMPS

logger = logging.getLogger(__name__)


def _extraire(nom_champ: str) -> str:
    debut, longueur = CHAMPS[nom_champ]
    return f"substring(ligne_source from {debut + 1} for {longueur})"


REQUETE = f"""
INSERT INTO silver.deces (
    nom, prenoms, sexe, date_naissance, code_lieu_naissance,
    commune_naissance, pays_naissance, date_deces, code_lieu_deces,
    numero_acte_deces, cle_rapprochement, fichier_source
)
SELECT DISTINCT ON (cle_naturelle)
    nom, prenoms, sexe, date_naissance, code_lieu_naissance,
    commune_naissance, pays_naissance, date_deces, code_lieu_deces,
    numero_acte_deces,
    upper(unaccent(nom)) || '|' || upper(unaccent(split_part(prenoms, ' ', 1)))
        || '|' || to_char(date_naissance, 'YYYYMMDD') AS cle_rapprochement,
    fichier_source
FROM (
    SELECT
        trim(split_part({_extraire("nom_prenoms")}, '*', 1))                     AS nom,
        trim(replace(split_part({_extraire("nom_prenoms")}, '*', 2), '/', ' '))   AS prenoms,
        nullif(trim({_extraire("sexe")}), '')::smallint                           AS sexe,
        to_date(nullif(regexp_replace({_extraire("date_naissance")}, '(00)$', '01'), ''),
                'YYYYMMDD')                                                       AS date_naissance,
        trim({_extraire("code_lieu_naissance")})                                  AS code_lieu_naissance,
        trim({_extraire("commune_naissance")})                                    AS commune_naissance,
        trim({_extraire("pays_naissance")})                                       AS pays_naissance,
        to_date(regexp_replace({_extraire("date_deces")}, '(00)$', '01'),
                'YYYYMMDD')                                                       AS date_deces,
        trim({_extraire("code_lieu_deces")})                                      AS code_lieu_deces,
        trim({_extraire("numero_acte_deces")})                                    AS numero_acte_deces,
        fichier_source,
        {_extraire("nom_prenoms")} || {_extraire("date_deces")}
            || {_extraire("numero_acte_deces")}                                   AS cle_naturelle
    FROM bronze.deces_brut
    WHERE run_id = %(run_id)s
      AND length(ligne_source) >= 176
) AS decoupe
WHERE date_deces IS NOT NULL
ORDER BY cle_naturelle
ON CONFLICT DO NOTHING;
"""


def promouvoir(run_id: str) -> int:
    import psycopg

    with psycopg.connect(CONFIG.pg_dsn) as connexion:
        with connexion.cursor() as curseur:
            curseur.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")
            curseur.execute(REQUETE, {"run_id": run_id})
            total = curseur.rowcount
        connexion.commit()

    logger.info("Silver : %d lignes promues pour l'exécution %s", total, run_id)
    return total
