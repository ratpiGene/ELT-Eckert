#!/bin/bash
# Rôles applicatifs de l'entrepôt (C4.2.1 — sécurité / modalités d'accès).
# Moindre privilège, trois rôles : un qui administre, un qui écrit, un qui lit.
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname eckert <<-EOSQL
    CREATE ROLE eckert_admin LOGIN PASSWORD '${ELT_ADMIN_PASSWORD}';
    CREATE ROLE elt_writer LOGIN PASSWORD '${ELT_WRITER_PASSWORD}';
    CREATE ROLE elt_reader LOGIN PASSWORD '${ELT_READER_PASSWORD}';
EOSQL
# Extension de normalisation utilisée par la promotion silver (droit réservé au superuser).
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname eckert -c "CREATE EXTENSION IF NOT EXISTS unaccent;"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname eckert -f /sql/10_schemas.sql
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname eckert -f /sql/20_tables.sql
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname eckert -f /sql/30_vues_gold.sql
