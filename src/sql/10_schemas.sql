-- ---------------------------------------------------------------------------
-- C4.2.1 — Organisation des données en trois couches et droits associés.
--
--   bronze : image fidèle de la source, aucune transformation, traçable
--   silver : données typées, nettoyées, dédoublonnées, conformes au contrat
--   gold   : données exposées au métier (rapprochements, indicateurs)
--
-- Modalités d'accès (trois rôles, moindre privilège) :
--   eckert_admin  administre les objets et les droits (DDL) — le DBA « gatekeeper »
--   elt_writer    alimente (le pipeline)
--   elt_reader    consomme la couche gold uniquement (le métier)
-- Le métier n'a jamais accès au brut.
-- ---------------------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS ops;      -- journal technique, qualité, supervision

-- Administration : le DBA « gatekeeper » du SI d'origine, reconstruit ici.
-- Gère la structure (DDL) et les droits sur toutes les couches.
GRANT ALL ON SCHEMA bronze, silver, gold, ops TO eckert_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA bronze, silver, gold, ops
    GRANT ALL ON TABLES TO eckert_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA bronze, silver, gold, ops
    GRANT ALL ON SEQUENCES TO eckert_admin;

-- Écriture : le pipeline
GRANT USAGE, CREATE ON SCHEMA bronze, silver, gold, ops TO elt_writer;
ALTER DEFAULT PRIVILEGES IN SCHEMA bronze, silver, gold, ops
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO elt_writer;
-- Les colonnes BIGSERIAL (bronze.deces_brut, silver.deces) s'appuient sur des
-- séquences : l'écriture par COPY/INSERT exige USAGE sur ces séquences.
ALTER DEFAULT PRIVILEGES IN SCHEMA bronze, silver, gold, ops
    GRANT USAGE, SELECT ON SEQUENCES TO elt_writer;

-- Lecture : la restitution métier, sur gold seulement
GRANT USAGE ON SCHEMA gold TO elt_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA gold GRANT SELECT ON TABLES TO elt_reader;

-- Refus explicite sur les couches techniques (testé dans tests/test_securite.py)
REVOKE ALL ON SCHEMA bronze, silver, ops FROM elt_reader;
