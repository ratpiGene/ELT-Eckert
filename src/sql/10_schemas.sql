-- ---------------------------------------------------------------------------
-- C4.2.1 — Organisation des données en trois couches et droits associés.
--
--   bronze : image fidèle de la source, aucune transformation, traçable
--   silver : données typées, nettoyées, dédoublonnées, conformes au contrat
--   gold   : données exposées au métier (rapprochements, indicateurs)
--
-- Modalités d'accès : elt_writer alimente, elt_reader consomme la couche gold
-- uniquement. Le métier n'a jamais accès au brut.
-- ---------------------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS ops;      -- journal technique, qualité, supervision

-- Écriture : le pipeline
GRANT USAGE, CREATE ON SCHEMA bronze, silver, gold, ops TO elt_writer;
ALTER DEFAULT PRIVILEGES IN SCHEMA bronze, silver, gold, ops
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO elt_writer;

-- Lecture : la restitution métier, sur gold seulement
GRANT USAGE ON SCHEMA gold TO elt_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA gold GRANT SELECT ON TABLES TO elt_reader;

-- Refus explicite sur les couches techniques (testé dans tests/test_securite.py)
REVOKE ALL ON SCHEMA bronze, silver, ops FROM elt_reader;
