-- Exécuté une seule fois, à la création du volume Postgres.
-- Deux bases sur une même instance : métastore Airflow et entrepôt métier.
CREATE DATABASE airflow;
CREATE DATABASE eckert;
