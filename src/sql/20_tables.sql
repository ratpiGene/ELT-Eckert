-- ---------------------------------------------------------------------------
-- C4.2.1 — Schéma de données
-- ---------------------------------------------------------------------------

-- BRONZE : la ligne source telle que reçue, plus sa traçabilité.
CREATE TABLE IF NOT EXISTS bronze.deces_brut (
    id              BIGSERIAL PRIMARY KEY,
    ligne_source    TEXT        NOT NULL,
    fichier_source  TEXT        NOT NULL,
    ligne_numero    INTEGER     NOT NULL,
    ingere_le       TIMESTAMPTZ NOT NULL DEFAULT now(),
    run_id          TEXT        NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_deces_brut_run ON bronze.deces_brut (run_id);

-- SILVER : données typées et validées.
CREATE TABLE IF NOT EXISTS silver.deces (
    id                    BIGSERIAL PRIMARY KEY,
    nom                   TEXT,
    prenoms               TEXT,
    sexe                  SMALLINT,
    date_naissance        DATE,
    code_lieu_naissance   TEXT,
    commune_naissance     TEXT,
    pays_naissance        TEXT,
    date_deces            DATE        NOT NULL,
    code_lieu_deces       TEXT,
    numero_acte_deces     TEXT,
    cle_rapprochement     TEXT        NOT NULL,
    fichier_source        TEXT        NOT NULL,
    charge_le             TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_deces_cle ON silver.deces (cle_rapprochement);
CREATE INDEX IF NOT EXISTS ix_deces_date ON silver.deces (date_deces);

-- SILVER : référentiel adhérents SYNTHÉTIQUE (aucune donnée réelle).
CREATE TABLE IF NOT EXISTS silver.adherent (
    adherent_id       BIGINT PRIMARY KEY,
    nom               TEXT NOT NULL,
    prenoms           TEXT NOT NULL,
    sexe              SMALLINT,
    date_naissance    DATE NOT NULL,
    code_insee_naiss  TEXT,
    cle_rapprochement TEXT NOT NULL,
    statut            TEXT NOT NULL DEFAULT 'ACTIF'
);
CREATE INDEX IF NOT EXISTS ix_adherent_cle ON silver.adherent (cle_rapprochement);

CREATE TABLE IF NOT EXISTS silver.contrat (
    contrat_id     BIGINT PRIMARY KEY,
    adherent_id    BIGINT NOT NULL REFERENCES silver.adherent (adherent_id),
    date_effet     DATE   NOT NULL,
    date_fin       DATE,
    capital_garanti NUMERIC(12,2),
    statut         TEXT   NOT NULL DEFAULT 'EN_COURS'
);
CREATE INDEX IF NOT EXISTS ix_contrat_adherent ON silver.contrat (adherent_id);

-- GOLD : le résultat métier — contrats potentiellement en déshérence.
CREATE TABLE IF NOT EXISTS gold.contrat_desherence (
    contrat_id        BIGINT      NOT NULL,
    adherent_id       BIGINT      NOT NULL,
    nom               TEXT,
    prenoms           TEXT,
    date_naissance    DATE,
    date_deces        DATE        NOT NULL,
    jours_depuis_deces INTEGER    NOT NULL,
    niveau_confiance  TEXT        NOT NULL,   -- CERTAIN | PROBABLE | A_VERIFIER
    capital_garanti   NUMERIC(12,2),
    detecte_le        TIMESTAMPTZ NOT NULL DEFAULT now(),
    run_id            TEXT        NOT NULL,
    PRIMARY KEY (contrat_id, run_id)
);
CREATE INDEX IF NOT EXISTS ix_desherence_confiance ON gold.contrat_desherence (niveau_confiance);

-- OPS : journal d'exécution et qualité (C4.3.1 — indicateurs supervisés).
CREATE TABLE IF NOT EXISTS ops.journal_execution (
    run_id            TEXT        NOT NULL,
    etape             TEXT        NOT NULL,
    statut            TEXT        NOT NULL,   -- SUCCES | ECHEC | ALERTE
    lignes_lues       BIGINT,
    lignes_rejetees   BIGINT,
    duree_secondes    NUMERIC(10,2),
    message           TEXT,
    horodatage        TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (run_id, etape, horodatage)
);

CREATE TABLE IF NOT EXISTS ops.controle_qualite (
    run_id       TEXT        NOT NULL,
    controle     TEXT        NOT NULL,
    resultat     TEXT        NOT NULL,   -- OK | KO
    valeur       TEXT,
    seuil        TEXT,
    horodatage   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (run_id, controle, horodatage)
);
