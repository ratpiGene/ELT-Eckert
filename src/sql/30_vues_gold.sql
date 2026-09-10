-- ---------------------------------------------------------------------------
-- C4.2.1 — Restitution métier : vue gold accessible au rôle de lecture.
--
-- Le métier n'interroge jamais les couches techniques. Il consomme cette vue,
-- qui priorise les contrats à instruire : d'abord les correspondances certaines,
-- puis les plus anciens décès (le délai Eckert court), puis les plus gros
-- capitaux. La colonne priorite donne un ordre d'instruction directement
-- exploitable.
-- ---------------------------------------------------------------------------

CREATE OR REPLACE VIEW gold.v_contrats_a_instruire AS
SELECT
    row_number() OVER (
        ORDER BY
            CASE niveau_confiance
                WHEN 'CERTAIN'    THEN 1
                WHEN 'PROBABLE'   THEN 2
                WHEN 'A_VERIFIER' THEN 3
            END,
            jours_depuis_deces DESC,
            capital_garanti DESC
    )                       AS priorite,
    contrat_id,
    adherent_id,
    nom,
    prenoms,
    date_deces,
    jours_depuis_deces,
    niveau_confiance,
    capital_garanti,
    run_id,
    detecte_le
FROM gold.contrat_desherence;

-- Le métier lit la vue ; il n'a aucun accès au brut ni au silver.
GRANT SELECT ON gold.v_contrats_a_instruire TO elt_reader;
