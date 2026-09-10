#!/bin/bash
# Rôles applicatifs de l'entrepôt (C4.2.1 — sécurité / modalités d'accès).
# Principe du moindre privilège : un rôle qui écrit, un rôle qui lit.
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname eckert <<-EOSQL
    CREATE ROLE elt_writer LOGIN PASSWORD '${ELT_WRITER_PASSWORD}';
    CREATE ROLE elt_reader LOGIN PASSWORD '${ELT_READER_PASSWORD}';
EOSQL
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname eckert -f /sql/10_schemas.sql
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname eckert -f /sql/20_tables.sql
